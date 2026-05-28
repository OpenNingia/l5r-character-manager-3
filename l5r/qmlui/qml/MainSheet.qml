// Copyright (C) 2014-2026 Daniele Simonetti
// Prototype "scrollable sheet" navigation: every section stacked
// vertically in one long scroll; a left-hand TOC tracks the currently
// visible section and jumps to others on click.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "widgets" as Widgets
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
    // The whole client area is parchment now -- no OS-grey desk under
    // the panels. The menubar above still follows the OS theme so the
    // window chrome stays native.
    color: Theme.parchment

    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            MenuItem {
                text: qsTr("&New")
                onTriggered: appCtrl.fileNew()
            }
            MenuItem {
                text: qsTr("&Open...")
                onTriggered: appCtrl.fileOpenDialog()
            }
            MenuItem {
                text: qsTr("&Save")
                onTriggered: appCtrl.fileSave()
            }
            MenuItem {
                text: qsTr("Save &As...")
                onTriggered: appCtrl.fileSaveAs()
            }
            MenuSeparator {
            }
            MenuItem {
                text: qsTr("&Quit")
                onTriggered: appCtrl.fileQuit()
            }
        }
    }

    // Children of `sheetColumn` are SectionBlock items in the same order
    // as appCtrl.tabs. We use sheetRepeater.itemAt(i) to read each one's
    // y coordinate, which the Column layout supplies for us.
    function sectionY(index) {
        var item = sheetRepeater.itemAt(index);
        return item ? item.y : 0;
    }

    function activeSectionFromContentY(y) {
        // 60px lookahead: a section becomes "active" just before its top
        // hits the viewport top.
        var probe = y + 60;
        var active = 0;
        for (var i = 0; i < sheetRepeater.count; ++i) {
            if (sectionY(i) <= probe) {
                active = i;
            } else {
                break;
            }
        }
        return active;
    }

    function jumpTo(index) {
        var target = sectionY(index);
        var maxY = Math.max(0, flick.contentHeight - flick.height);
        scrollAnim.to = Math.min(target, maxY);
        scrollAnim.restart();
    }

    NumberAnimation {
        id: scrollAnim
        target: flick
        property: "contentY"
        duration: 220
        easing.type: Easing.OutQuad
    }

    // Outer Pane owns the parchment background, the rice-paper fibre
    // texture, and the ink-on-paper palette overrides. The palette
    // descends to every Control/Label inside (TOC delegates, section
    // bodies, dialogs) so we don't need to repeat the overrides
    // per-SheetPanel -- the SheetPanel ones become defensive defaults
    // for when a panel is used outside this window (e.g. tests).
    Pane {
        anchors.fill: parent
        padding: 0
        palette.windowText: Theme.ink
        palette.text: Theme.ink
        palette.buttonText: Theme.ink
        palette.base: Theme.parchmentBase
        palette.alternateBase: Theme.parchmentInset
        palette.placeholderText: "#8a7a65"
        palette.mid: "#a89580"

        background: Rectangle {
            color: Theme.parchment
            // Window-wide fibre overlay -- continuous across panels
            // and gutters so the whole sheet feels like one piece of
            // paper.
            Widgets.RicePaperOverlay {
            }
        }

        RowLayout {
            anchors.fill: parent
            spacing: 0

            // ---- Left TOC --------------------------------------------------
            Rectangle {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                // Slightly darker parchment than the main sheet so the
                // navigation column reads as a distinct zone without
                // breaking the "one document" illusion.
                color: Theme.parchmentSidebar

                // Same fibre texture as the main sheet so the sidebar
                // reads as the same paper, just a darker shade -- not a
                // flat coloured panel glued onto the document.
                Widgets.RicePaperOverlay {
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.topMargin: 14
                    anchors.bottomMargin: 8
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 6

                    // ---- Identity block ----------------------------------
                    // Three-line character header above the TOC: name in
                    // burnt-gold display type, clan + rank as a single
                    // secondary line, school italicised underneath. Reads
                    // like the title block of a character sheet rather
                    // than a piece of chrome.
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1

                        Label {
                            Layout.fillWidth: true
                            text: (pcProxy && pcProxy.name) ? pcProxy.name : qsTr("Unnamed")
                            font.family: Theme.fontDisplay
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                            font.letterSpacing: 0.5
                            color: Theme.heading
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Label {
                            Layout.fillWidth: true
                            readonly property string _clan: (pcProxy && pcProxy.clan) ? pcProxy.clan : ""
                            readonly property int _rank: pcProxy ? pcProxy.progression.rank : 0
                            text: {
                                var clanFmt = _clan ? _clan.charAt(0).toUpperCase() + _clan.slice(1) : qsTr("No Clan");
                                return clanFmt + " — " + qsTr("Rank %1").arg(_rank);
                            }
                            font.pixelSize: Theme.bodyFont
                            font.features: Theme.tabularNumbers
                            color: palette.windowText
                            opacity: 0.85
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Label {
                            Layout.fillWidth: true
                            text: (pcProxy && pcProxy.school) ? pcProxy.school : qsTr("No School")
                            font.pixelSize: Theme.smallFont
                            font.italic: true
                            color: palette.windowText
                            opacity: 0.7
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    Widgets.OrnateDivider {
                        Layout.fillWidth: true
                        Layout.topMargin: 4
                        Layout.bottomMargin: 2
                    }

                    ListView {
                        id: toc
                        Layout.fillWidth: true
                        Layout.fillHeight: true
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
                                toc.currentIndex = index;
                                root.jumpTo(index);
                            }

                            // Strip the default Control background -- without
                            // this override, ItemDelegate paints a palette-
                            // driven fill that reads as flat grey on top of
                            // the parchment sidebar.  Hover gets a warm wash
                            // (lighter parchment), idle is fully transparent
                            // so the sidebar texture shows through.
                            background: Rectangle {
                                color: tocDelegate.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.07) : "transparent"
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
                                // Brush-script kanji; the Hakushū Higerei face
                                // has heavier strokes than a system CJK font
                                // so 20px is comfortable here without crowding
                                // the column.
                                Label {
                                    text: modelData.icon
                                    font.family: Theme.fontKanji
                                    font.pixelSize: 22
                                    Layout.leftMargin: 14
                                    Layout.preferredWidth: 28
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

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }

                onContentYChanged: {
                    // Don't fight the user's click-to-jump animation.
                    if (!scrollAnim.running) {
                        toc.currentIndex = root.activeSectionFromContentY(contentY);
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
}
