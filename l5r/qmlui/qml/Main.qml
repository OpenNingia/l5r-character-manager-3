// Copyright (C) 2014-2026 Daniele Simonetti
// Skeleton QML root for the L5RCM dual-UI experiment.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 900
    height: 720
    visible: true
    title: pcProxy.displayTitle

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
            MenuSeparator {}
            MenuItem {
                text: qsTr("&Quit")
                onTriggered: appCtrl.fileQuit()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Repeater {
                model: appCtrl.tabs
                TabButton { text: modelData.icon + "  " + modelData.title }
            }
        }

        StackLayout {
            id: tabStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex
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
