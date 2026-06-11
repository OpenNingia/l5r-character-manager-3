// Copyright (C) 2014-2026 Daniele Simonetti
// A row of small clickable dots representing a 0..N point pool.
// QML replacement for l5r.widgets.CkNumWidget used on the Character
// tab for the void-points pool and the social-flag point trackers.
// Interactions:
//   * click dot          -> request value (index + 1); click the top dot
//                           again to request `index` (matches CkNumWidget).
//   * shift+click dot    -> emit `rankBumpRequested()` so the parent can
//                           advance the underlying rank.
//   * wheel up / down    -> request ±1, clamped to [0, count]. With
//                           `wrap: true`, scrolling past either end emits
//                           `wrapRequested(±1)` instead so the parent can
//                           roll the rank over (e.g. 5.9 -> 6.0).
// Like RankStepper, this widget is SIGNAL-ONLY: it emits `valueRequested`
// and never assigns its own `value`. The parent owns `value` via a binding
// to the model, so the dots always track live model state. (Self-assigning
// here would break that binding and freeze the dots -- e.g. they'd keep a
// stale fill after File>New or loading a character.)
//   * hover              -> the dot under the cursor gently scales up.
// Styling: filled dots take `accent`; empty dots also use `accent` for
// the border so the track reads as a single colour-themed row (e.g.
// the honor track in green, infamy in red, void in purple). `dotSize`
// is parametric so compact contexts (Shadowlands/Infamy on the social
// panel) can ship a smaller variant without forking the widget.
// `showDigits` prints each dot's value (1..count) inside the dot --
// the social tracks use it to spell out that the dots are the tenths
// of the rank (design §6.12, issue #402).
import QtQuick
import QtQuick.Layouts
import Theme 1.0

Row {
    id: track
    property int count: 10
    property int value: 0
    property int dotSize: Theme.pointDotSize
    property color accent: Theme.accent
    property bool showDigits: false
    // When true, wheel-scrolling past either end emits wrapRequested
    // instead of clamping, so the parent can roll an adjacent rank.
    property bool wrap: false
    signal rankBumpRequested
    signal wrapRequested(int direction)
    // Emitted on user interaction with the requested new value. The widget
    // does NOT assign `value` itself -- the parent commits to the model and
    // the `value` binding flows the result back (see header note).
    signal valueRequested(int requested)
    spacing: Theme.pointDotSpacing

    // Scroll-wheel fine adjustment. Sits on the Row so the wheel zone
    // covers the gaps between dots, not just the dot interiors.
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function (event) {
            var step = event.angleDelta.y > 0 ? 1 : -1;
            var newValue = track.value + step;
            if (track.wrap && (newValue > track.count || newValue < 0)) {
                track.wrapRequested(step);
            } else {
                newValue = Math.max(0, Math.min(track.count, newValue));
                if (newValue !== track.value) {
                    track.valueRequested(newValue);
                }
            }
            event.accepted = true;
        }
    }

    Repeater {
        model: track.count
        delegate: Rectangle {
            id: dot
            width: track.dotSize
            height: track.dotSize
            radius: track.dotSize / 2
            border.width: 1.5
            border.color: index < track.value ? Qt.darker(track.accent, 1.4) : track.accent
            color: index < track.value ? track.accent : "transparent"
            // Center-anchored hover scale -- transform.origin defaults
            // to (width/2, height/2) so neighbours don't shift.
            scale: ma.containsMouse ? 1.25 : 1.0
            Behavior on scale  {
                NumberAnimation {
                    duration: 90
                }
            }

            // The dot's own value (1..count) printed inside it -- on
            // the social tracks this reads as ".1 .2 .3", making it
            // explicit that the dots are the tenths of the rank.
            Text {
                visible: track.showDigits
                anchors.centerIn: parent
                text: index + 1
                font.family: Theme.fontStat
                font.pixelSize: Theme.pointDotDigitSize
                color: index < track.value ? Theme.parchment : track.accent
            }

            MouseArea {
                id: ma
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: function (mouse) {
                    if (mouse.modifiers & Qt.ShiftModifier) {
                        track.rankBumpRequested();
                        return;
                    }
                    var newValue = (track.value === index + 1) ? index : index + 1;
                    if (newValue !== track.value) {
                        track.valueRequested(newValue);
                    }
                }
            }
        }
    }
}
