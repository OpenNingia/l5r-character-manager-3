// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system toggle switch (§6.8). A parchment-skinned Switch: a
// 44x24 pill track that fills burnt-gold when on, a cream thumb that
// slides across, and an optional caption to the *left* of the track.
//
// Built on Quick Controls' Switch so we inherit checked/toggled,
// keyboard focus and accessibility for free, and only re-skin the
// indicator + contentItem (the Fusion style honours these overrides;
// the native Windows style would not -- see the QML invariant).
//
// Usage:
//   Widgets.L5RToggle {
//       checked: appSettings ? appSettings.firstPageSkills : false
//       onToggled: appSettings.setFirstPageSkills(checked)
//   }
//   Widgets.L5RToggle { text: qsTr("Override"); checked: ... }
import QtQuick
import QtQuick.Controls
import Theme 1.0

Switch {
    id: control

    // Track + thumb metrics are fixed by §6.8 (44x24, r12; 20px thumb
    // with a 2px inset). These are component-local control metrics, not
    // part of the global spacing scale.
    spacing: Theme.s2   // gap between caption and track (8px, §6.8)
    implicitHeight: 24

    // The pill track. Anchored to the right edge of the control so the
    // optional caption sits to its left; when there is no caption the
    // control's implicit width equals the track width, so x resolves to 0.
    indicator: Rectangle {
        id: track
        implicitWidth: 44
        implicitHeight: 24
        radius: height / 2
        x: control.width - width
        y: (control.height - height) / 2
        color: control.checked ? Theme.heading : Theme.disabledBg
        Behavior on color {
            ColorAnimation { duration: Theme.durBase }
        }

        Rectangle {
            id: thumb
            width: 20
            height: 20
            radius: height / 2
            y: 2
            x: control.checked ? track.width - width - 2 : 2
            color: Theme.whiteWash
            Behavior on x {
                NumberAnimation {
                    duration: Theme.durBase
                    easing.type: Easing.InOutQuad
                }
            }
        }
    }

    // Optional caption, left of the track (§6.8: --text-caption,
    // --color-ink-muted). Reserves the track + gap on its right so the
    // two never overlap; collapses to zero width when there is no text.
    contentItem: Label {
        text: control.text
        visible: control.text.length > 0
        font.family: Theme.fontBody
        font.pixelSize: Theme.fsCaption
        color: Theme.inkMuted
        verticalAlignment: Text.AlignVCenter
        rightPadding: control.indicator.width + control.spacing
    }
}
