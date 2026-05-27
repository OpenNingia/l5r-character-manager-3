// Copyright (C) 2014-2026 Daniele Simonetti
// A row of small clickable dots representing a 0..N point pool.
// QML replacement for l5r.widgets.CkNumWidget used on the Character
// tab for the void-points pool and the social-flag point trackers.
// Click a dot to set the value to (index + 1); click the same dot
// again to clear from that position onward (matches CkNumWidget).
//
// The dots use the shared Theme: filled dots take `accent` (defaults
// to Theme.accent so the caller can theme each row independently --
// e.g. honor track in green, infamy in red). Empty dots use
// Theme.borderStrong at full opacity so they read on both light and
// dark backgrounds (the previous palette.windowText/0.65 alpha
// vanished on certain themes).
import QtQuick
import QtQuick.Layouts

import Theme 1.0

Row {
    id: track
    property int count: 10
    property int value: 0
    property color accent: Theme.accent
    spacing: Theme.pointDotSpacing

    Repeater {
        model: track.count
        delegate: Rectangle {
            width: Theme.pointDotSize
            height: Theme.pointDotSize
            radius: Theme.pointDotSize / 2
            border.width: 1.5
            border.color: index < track.value
                ? Qt.darker(track.accent, 1.4)
                : Theme.borderStrong
            color: index < track.value ? track.accent : "transparent"

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    // Toggle: clicking the rightmost filled dot clears
                    // down to index; otherwise fills up to (index+1).
                    var newValue = (track.value === index + 1) ? index
                                                               : index + 1
                    if (newValue !== track.value) {
                        track.value = newValue
                    }
                }
            }
        }
    }
}
