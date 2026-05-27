// Copyright (C) 2014-2026 Daniele Simonetti
// Prototype "left rail" navigation: fixed-width sidebar on the left
// with icon + label per section, content fills the rest of the window.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1000
    height: 720
    visible: true
    title: pcProxy.displayTitle

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

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ---- Left rail -------------------------------------------------
        Rectangle {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            // Inherit the window bg; rely on the 1px divider on the
            // right to demarcate the rail. Tinting via palette.alternateBase
            // can read too dark on themes where its value diverges from
            // palette.window.
            color: "transparent"

            ListView {
                id: railList
                anchors.fill: parent
                anchors.topMargin: 8
                anchors.bottomMargin: 8
                model: appCtrl.tabs
                clip: true
                currentIndex: 0
                spacing: 2
                boundsBehavior: Flickable.StopAtBounds

                delegate: ItemDelegate {
                    id: railDelegate
                    width: ListView.view.width
                    height: 44
                    highlighted: ListView.isCurrentItem
                    onClicked: railList.currentIndex = index

                    // When highlighted the ItemDelegate background becomes
                    // palette.highlight; bind label colors to the matching
                    // highlightedText so we never end up with dark-on-dark
                    // or light-on-light.
                    contentItem: RowLayout {
                        spacing: 12
                        Label {
                            text: modelData.icon
                            font.pixelSize: 20
                            Layout.leftMargin: 14
                            Layout.preferredWidth: 24
                            horizontalAlignment: Text.AlignHCenter
                            color: railDelegate.highlighted ? palette.highlightedText : palette.windowText
                            opacity: railDelegate.highlighted ? 1.0 : 0.75
                        }
                        Label {
                            text: modelData.title
                            font.pixelSize: 13
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: railDelegate.highlighted ? palette.highlightedText : palette.windowText
                            font.weight: railDelegate.highlighted ? Font.DemiBold : Font.Normal
                        }
                    }
                }
            }
        }

        // ---- Divider ---------------------------------------------------
        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: palette.mid
            opacity: 0.45
        }

        // ---- Content ---------------------------------------------------
        StackLayout {
            id: railStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: railList.currentIndex
            Repeater {
                model: appCtrl.tabs
                TabPlaceholder {
                    tabId: modelData.id
                    title: modelData.title
                    icon: modelData.icon
                }
            }
        }
    }
}
