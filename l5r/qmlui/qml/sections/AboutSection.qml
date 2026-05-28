// Copyright (C) 2014-2026 Daniele Simonetti
// Read-only About page: logo + app title + version, a few paragraphs of
// links (project page, bug tracker, AEG, L5R RPG home), and a footer.
// Layout-agnostic ColumnLayout: embedded inside a SectionBlock body.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

ColumnLayout {
    id: about
    // appCtrl reads as null on the first binding pass (see MainSheet.qml
    // note); the guard keeps the engine quiet at launch.
    readonly property var info: appCtrl ? appCtrl.aboutInfo : ({})
    spacing: 18

    RowLayout {
        Layout.fillWidth: true
        spacing: 24

        Image {
            source: about.info.iconUrl
            sourceSize.width: 64
            sourceSize.height: 64
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            Layout.alignment: Qt.AlignTop
            fillMode: Image.PreserveAspectFit
            asynchronous: true
        }

        ColumnLayout {
            spacing: 4
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter

            Label {
                text: about.info.appDesc
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.headerFont
                font.weight: Font.DemiBold
                color: Theme.heading
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            Label {
                text: qsTr("Version %1").arg(about.info.version)
                font.pixelSize: Theme.bodyFont
                color: Theme.accent
                opacity: 0.85
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Theme.divider
        opacity: Theme.dividerOpacity
    }

    Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        textFormat: Text.RichText
        color: palette.windowText
        linkColor: Theme.accent
        onLinkActivated: function (link) {
            Qt.openUrlExternally(link);
        }
        text: qsTr("<p><a href=\"%1\">%2</a></p>" + "<p>Report bugs and send in your ideas <a href=\"%3\">here</a>.</p>" + "<p>To learn more about Legend of the Five Rings, visit " + "<a href=\"%4\">the L5R RPG home page</a>.</p>" + "<p>All rights on Legend of the Five Rings RPG belong to " + "<a href=\"%5\">Fantasy Flight Games</a>.</p>" + "<p>Get the latest data packs " + "<a href=\"%6\">on GitHub</a>.</p>").arg(about.info.projectPage).arg(about.info.projectPageName).arg(about.info.bugtraq).arg(about.info.l5rRpgHome).arg(about.info.companyHome).arg(about.info.dataPacks)
    }

    Label {
        Layout.fillWidth: true
        text: qsTr("© 2015 %1").arg(about.info.author)
        opacity: 0.55
        font.pixelSize: 11
    }

    Label {
        Layout.fillWidth: true
        text: qsTr("Special thanks: Paul Tar Jr (Geiko) and Derrick D. Cochran.")
        wrapMode: Text.WordWrap
        opacity: 0.55
        font.pixelSize: 11
    }
}
