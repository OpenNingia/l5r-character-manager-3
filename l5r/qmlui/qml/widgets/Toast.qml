// Copyright (C) 2014-2026 Daniele Simonetti
// Transient in-window notice ("toast"). The design system has no toast
// spec, so every value here derives from Theme tokens: a white-wash
// bubble with a hairline sepia border and a burnt-gold left stripe
// (informational, not the crimson reserved for destructive/error), ink
// body text in IM Fell. It fades + slides up on show, dwells, then fades
// + slides back down -- the slide tracks opacity so one Behavior drives
// both. Used for "needs a restart" settings notices today; reusable for
// any short, non-blocking message.
//
// The consumer anchors this Item where the toast should rest (e.g.
// bottom-centred over the sheet) and calls show(text):
//   Widgets.Toast { id: toast; anchors.horizontalCenter: ...; anchors.bottom: ... }
//   toast.show(qsTr("Saved."))
import QtQuick
import QtQuick.Controls
import Theme 1.0

Item {
    id: toast

    property string message: ""
    // How long the toast stays fully visible before fading out. Not a
    // motion duration (§9) -- it's dwell/behaviour -- so it is a plain
    // tunable, defaulted here.
    property int dwellMs: 4000

    implicitWidth: bubble.implicitWidth
    implicitHeight: bubble.implicitHeight

    opacity: 0
    visible: opacity > 0.01

    // Slide tracks the fade: 10px below at rest, flush when shown.
    transform: Translate {
        y: (1 - toast.opacity) * 10
    }
    Behavior on opacity {
        NumberAnimation {
            duration: Theme.durBase
            easing.type: Easing.OutQuad
        }
    }

    function show(text) {
        toast.message = text;
        toast.opacity = 1;
        dwell.restart();
    }

    Timer {
        id: dwell
        interval: toast.dwellMs
        repeat: false
        onTriggered: toast.opacity = 0
    }

    Rectangle {
        id: bubble
        anchors.fill: parent
        // stripe + left margin + (capped) text + right margin. Driven by
        // the label's own width, which is capped below, so there is no
        // anchor/width cycle.
        implicitWidth: stripe.width + Theme.s4 + label.width + Theme.s4
        implicitHeight: label.implicitHeight + 2 * Theme.s3
        color: Theme.whiteWash
        border.color: Theme.borderSubtle
        border.width: 1
        radius: 4

        Rectangle {
            id: stripe
            width: 3
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            color: Theme.heading
            // Inset 1px so the stripe sits inside the bubble's border.
            anchors.margins: 1
        }

        Label {
            id: label
            anchors.left: stripe.right
            anchors.leftMargin: Theme.s4
            anchors.verticalCenter: parent.verticalCenter
            // Cap the line length so a long sentence wraps instead of
            // stretching the bubble across the whole window. implicitWidth
            // is the unwrapped natural width (independent of `width`), so
            // this min() does not feed back on itself.
            width: Math.min(implicitWidth, 460)
            text: toast.message
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
}
