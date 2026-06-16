// Copyright (C) 2014-2026 Daniele Simonetti
// DamageHealDialog -- QML-native form for inflicting or healing a batch of
// wounds at once. Replaces the per-1 +/- stepper that used to sit in the
// WoundsBlock header: that widget made the player click N times to apply a
// hit, which does not match how the game actually deals damage (a single
// roll inflicts many wounds at once). Opened from the WoundsBlock header
// button:
//     damageHealDlg.present()             // defaults to "inflict"
//
// A two-segment Inflict / Heal selector (default Inflict) flips the mode;
// the accent follows it -- crimson for damage, green for healing -- so the
// whole dialog reads at a glance as either harm or mending. The amount is a
// plain positive integer; on accept it is routed through
// appCtrl.damageHealth(+/-n) so the dirty flag + narrow wounds_changed
// signal stay correct (same path as the old stepper).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 420, 420)
    padding: Theme.s5

    // --- state ----------------------------------------------------
    // _heal == false  ->  inflict wounds (default)
    property bool _heal: false
    readonly property int _amount: parseInt(amountField.text, 10)
    readonly property bool _valid: !isNaN(_amount) && _amount > 0

    // Current / max wounds for the live preview of the resulting total.
    readonly property int _cur: pcProxy ? pcProxy.currentWounds : 0
    readonly property int _max: pcProxy ? pcProxy.maxWounds : 0
    readonly property int _result: {
        if (!_valid)
            return _cur;
        var n = _heal ? _cur - _amount : _cur + _amount;
        return Math.max(0, Math.min(n, _max));
    }

    // --- chrome (via L5RDialog) -----------------------------------
    // The accent (and seal) follow the mode: crimson 傷 (wound) for inflict,
    // green 治 (heal) for mending.
    readonly property color _accent: _heal ? Theme.positive : Theme.accent
    seal: _heal ? "治" : "傷"
    accent: _accent
    accentDark: Qt.darker(_accent, 1.3)
    title: _heal ? qsTr("Heal Wounds") : qsTr("Inflict Wounds")
    tagline: _heal ? qsTr("bind the body's hurts") : qsTr("the strike lands and the flesh remembers")
    acceptText: _heal ? qsTr("Heal") : qsTr("Inflict")
    acceptGlyph: _heal ? "治" : "傷"
    acceptEnabled: root._valid
    statusText: root._valid ? qsTr("Wounds: %1 → %2 of %3").arg(root._cur).arg(root._result).arg(root._max) : qsTr("Enter how many wounds to apply.")
    onAccepted: {
        if (!root._valid || !appCtrl)
            return;
        appCtrl.damageHealth(root._heal ? -root._amount : root._amount);
    }

    // --- entrypoint -----------------------------------------------
    // `heal` is optional; default mode is inflict.
    function present(heal) {
        root._heal = heal === true;
        amountField.text = "1";
        root.open();
        amountField.forceActiveFocus();
        amountField.selectAll();
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: Theme.s4

        // ---- Mode selector (Inflict | Heal) ----------------------
        // Two mutually-exclusive segments; `_heal` is the single source of
        // truth, so no ButtonGroup is needed (same shape as the element
        // tiles in ChooseElementDialog). The active segment fills with its
        // mode hue; the inactive one is outlined with a faint hover wash.
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s2

            Repeater {
                model: [
                    {
                        "heal": false,
                        "label": qsTr("Inflict"),
                        "hue": Theme.accent
                    },
                    {
                        "heal": true,
                        "label": qsTr("Heal"),
                        "hue": Theme.positive
                    }
                ]
                delegate: AbstractButton {
                    id: seg
                    required property var modelData
                    readonly property bool _on: root._heal === modelData.heal
                    Layout.fillWidth: true
                    implicitHeight: 38
                    onClicked: root._heal = modelData.heal

                    background: Rectangle {
                        radius: 3
                        color: seg._on ? seg.modelData.hue : (seg.hovered ? Qt.rgba(seg.modelData.hue.r, seg.modelData.hue.g, seg.modelData.hue.b, 0.12) : "transparent")
                        border.color: seg.modelData.hue
                        border.width: seg._on ? 0 : 1
                        Behavior on color {
                            ColorAnimation {
                                duration: Theme.durHover
                            }
                        }
                    }
                    contentItem: Label {
                        text: seg.modelData.label.toUpperCase()
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsLabel
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.2
                        color: seg._on ? Theme.whiteWash : Theme.ink
                    }
                }
            }
        }

        // ---- Amount ----------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Label {
                text: qsTr("AMOUNT")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }
            TextField {
                id: amountField
                Layout.fillWidth: true
                implicitHeight: 34
                text: "1"
                inputMethodHints: Qt.ImhDigitsOnly
                validator: IntValidator {
                    bottom: 1
                    top: 999
                }
                placeholderText: qsTr("number of wounds")
                color: Theme.ink
                placeholderTextColor: Theme.inkFaint
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsBody
                background: Rectangle {
                    color: Theme.parchmentBase
                    border.color: amountField.activeFocus ? root._accent : Theme.borderSubtle
                    border.width: 1
                    radius: 2
                }
                // Enter accepts when valid.
                onAccepted: {
                    if (root._valid)
                        root.accept();
                }
            }
        }
    }
}
