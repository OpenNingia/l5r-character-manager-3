// Copyright (C) 2014-2026 Daniele Simonetti
// Prototype "scrollable sheet" navigation: every section stacked
// vertically in one long scroll; a left-hand TOC tracks the currently
// visible section and jumps to others on click.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Theme 1.0

ApplicationWindow {
    id: root
    width: 1000
    height: 720
    visible: true
    // Null-guard the proxy refs: QML evaluates ApplicationWindow's
    // construction-time bindings before context properties are fully
    // wired, so pcProxy/appCtrl read as null on the first pass and
    // then resettle. Without the guard the engine logs a TypeError on
    // every launch.
    title: pcProxy ? pcProxy.displayTitle : ""

    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            MenuItem { text: qsTr("&New");        onTriggered: appCtrl.fileNew() }
            MenuItem { text: qsTr("&Open...");    onTriggered: appCtrl.fileOpenDialog() }
            MenuItem { text: qsTr("&Save");       onTriggered: appCtrl.fileSave() }
            MenuItem { text: qsTr("Save &As..."); onTriggered: appCtrl.fileSaveAs() }
            MenuSeparator {}
            MenuItem { text: qsTr("&Quit");       onTriggered: appCtrl.fileQuit() }
        }
    }

    // Children of `sheetColumn` are SectionBlock items in the same order
    // as appCtrl.tabs. We use sheetRepeater.itemAt(i) to read each one's
    // y coordinate, which the Column layout supplies for us.
    function sectionY(index) {
        var item = sheetRepeater.itemAt(index)
        return item ? item.y : 0
    }

    function activeSectionFromContentY(y) {
        // 60px lookahead: a section becomes "active" just before its top
        // hits the viewport top.
        var probe = y + 60
        var active = 0
        for (var i = 0; i < sheetRepeater.count; ++i) {
            if (sectionY(i) <= probe) {
                active = i
            } else {
                break
            }
        }
        return active
    }

    function jumpTo(index) {
        var target = sectionY(index)
        var maxY = Math.max(0, flick.contentHeight - flick.height)
        scrollAnim.to = Math.min(target, maxY)
        scrollAnim.restart()
    }

    NumberAnimation {
        id: scrollAnim
        target: flick
        property: "contentY"
        duration: 220
        easing.type: Easing.OutQuad
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ---- Left TOC --------------------------------------------------
        Rectangle {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            // Inherit the window bg so TOC labels can safely default to
            // palette.windowText. Differentiation comes from the 1px
            // divider on the right -- a tinted bg here was reading too
            // dark relative to the buttons on the user's theme.
            color: "transparent"

            ListView {
                id: toc
                anchors.fill: parent
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                model: appCtrl ? appCtrl.tabs : []
                clip: true
                currentIndex: 0
                spacing: 2
                interactive: true
                boundsBehavior: Flickable.StopAtBounds

                delegate: ItemDelegate {
                    id: tocDelegate
                    width: ListView.view.width
                    height: 38
                    highlighted: ListView.isCurrentItem
                    onClicked: {
                        toc.currentIndex = index
                        root.jumpTo(index)
                    }

                    // Active item: accent stripe on the left, accent
                    // icon, accent-tinted label.  Inactive: normal
                    // palette text colours so the OS theme is honoured.
                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 3
                        color: Theme.accent
                        visible: tocDelegate.highlighted
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Label {
                            text: modelData.icon
                            font.pixelSize: 16
                            Layout.leftMargin: 14
                            Layout.preferredWidth: 22
                            horizontalAlignment: Text.AlignHCenter
                            color: tocDelegate.highlighted ? Theme.accent : palette.windowText
                            opacity: tocDelegate.highlighted ? 1.0 : 0.7
                        }
                        Label {
                            text: modelData.title
                            font.pixelSize: 12
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: tocDelegate.highlighted ? Theme.accent : palette.windowText
                            font.weight: tocDelegate.highlighted ? Font.DemiBold : Font.Normal
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: Theme.divider
            opacity: Theme.dividerOpacity
        }

        // ---- Scrollable sheet -----------------------------------------
        Flickable {
            id: flick
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: sheetColumn.implicitHeight + 32
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            onContentYChanged: {
                // Don't fight the user's click-to-jump animation.
                if (!scrollAnim.running) {
                    toc.currentIndex = root.activeSectionFromContentY(contentY)
                }
            }

            Column {
                id: sheetColumn
                x: 16
                y: 16
                width: flick.width - 32
                spacing: 16

                Repeater {
                    id: sheetRepeater
                    model: appCtrl ? appCtrl.tabs : []
                    delegate: SectionBlock {
                        width: sheetColumn.width
                        tabId: modelData.id
                        title: modelData.title
                        icon: modelData.icon
                    }
                }
            }
        }
    }
}
