// Copyright (C) 2014-2026 Daniele Simonetti
// QrShareDialog -- shares the active character with the Android companion
// app as an animated loop of QR codes. The companion scans the loop with
// its camera until it has collected every frame, then reassembles and
// imports the .l5r (see docs/QR_IMPORT_FORMAT.md).
//
// Opened from the File menu (MainSheet). On open it pulls the frame
// strings from appCtrl.qrFrames() -- one QR per frame -- and cycles them
// at ~5 fps. The frames are rendered to images by the "qr" image provider
// registered on the engine (l5r/qmlui/proxies/qr_image_provider.py); the
// frame text is the URL-encoded image id.
//
// Single-action modal: just "Close" (acceptVisible/cancelVisible on the
// shared L5RDialog shell). 印 (in, a seal/stamp) is the header glyph --
// the character is being "stamped" into a scannable code.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 420, 420)
    padding: Theme.s6

    // Frame strings for the current transfer + the cursor into them.
    property var frames: []
    property int currentIndex: 0
    readonly property bool hasFrames: frames && frames.length > 0
    // Display edge of the QR symbol; the provider renders to this size.
    readonly property int qrEdge: 300

    title: qsTr("Share via QR code")
    tagline: qsTr("Import into the companion app")
    seal: "印"
    accent: Theme.accent
    accentDark: Theme.accentMuted
    // Single action: a plain Close. Cancel is hidden; the primary button
    // just dismisses.
    cancelVisible: false
    acceptText: qsTr("Close")

    // Pull a fresh transfer every time the dialog is shown (a new random
    // transfer id, current character state) and restart the loop from the
    // first frame.
    onOpened: {
        frames = appCtrl ? appCtrl.qrFrames() : [];
        currentIndex = 0;
    }
    onClosed: frames = []

    // Advance the loop only while visible and only when there is more than
    // one frame (a single-frame transfer is a static QR).
    Timer {
        interval: 200   // ~5 fps, the spec's recommended cadence
        running: root.visible && root.frames.length > 1
        repeat: true
        onTriggered: root.currentIndex = (root.currentIndex + 1) % root.frames.length
    }

    ColumnLayout {
        width: parent.width
        spacing: Theme.s4

        // --- Empty state: no active character / no frames ----------------
        Label {
            Layout.fillWidth: true
            visible: !root.hasFrames
            text: qsTr("There is nothing to share yet. Create or open a "
                + "character first.")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.inkMuted
        }

        // --- QR symbol on a white card (black-on-white for scanning) -----
        Rectangle {
            visible: root.hasFrames
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: root.qrEdge + Theme.s4 * 2
            Layout.preferredHeight: root.qrEdge + Theme.s4 * 2
            radius: 4
            color: "#ffffff"
            border.color: Theme.borderSubtle
            border.width: 1

            Image {
                anchors.centerIn: parent
                width: root.qrEdge
                height: root.qrEdge
                // Crisp modules: no smoothing, render at the exact display
                // size. The frame text is URL-encoded into the provider id
                // (it contains |, +, / and = which are not URL-safe).
                smooth: false
                sourceSize.width: root.qrEdge
                sourceSize.height: root.qrEdge
                fillMode: Image.PreserveAspectFit
                source: root.hasFrames
                    ? "image://qr/" + encodeURIComponent(root.frames[root.currentIndex])
                    : ""
            }
        }

        // --- Frame counter (only meaningful for multi-frame transfers) ---
        Label {
            visible: root.hasFrames && root.frames.length > 1
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Frame %1 of %2").arg(root.currentIndex + 1)
                                        .arg(root.frames.length)
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatSmall
            font.features: Theme.tabularNumbers
            color: Theme.inkMuted
        }

        // --- Instructions ------------------------------------------------
        Label {
            visible: root.hasFrames
            Layout.fillWidth: true
            text: root.frames.length > 1
                ? qsTr("Open the companion app and point its camera at this "
                    + "code. Keep the window in view — the frames cycle "
                    + "automatically until every part has been scanned.")
                : qsTr("Open the companion app and point its camera at this "
                    + "code to import the character.")
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsCaption
            color: Theme.inkMuted
        }
    }
}
