// Copyright (C) 2014-2026 Daniele Simonetti
// Placeholder used by the tab + rail layouts: a centered, illustrative
// stand-in for tab content that has not been ported yet. Sized so the
// surrounding chrome doesn't collapse on small windows.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Pane {
    id: placeholder
    property string tabId: ""
    property string title: ""
    property string icon: ""

    padding: 24

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 12
        width: Math.min(parent.width - 48, 480)

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: placeholder.icon
            font.pixelSize: 64
            opacity: 0.55
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: placeholder.title || placeholder.tabId
            font.pixelSize: 22
            font.weight: Font.DemiBold
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Tab '%1' coming soon").arg(placeholder.tabId)
            font.pixelSize: 13
            opacity: 0.6
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 320
            Layout.preferredHeight: 1
            color: palette.mid
            opacity: 0.4
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 360
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("Real content lands in a follow-up PR. The layout you see now is just navigation chrome.")
            font.pixelSize: 12
            opacity: 0.55
        }
    }
}
