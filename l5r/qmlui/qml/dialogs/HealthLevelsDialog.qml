// Copyright (C) 2014-2026 Daniele Simonetti
// HealthLevelsDialog -- edits the two multipliers that shape the wound
// table, consolidated off the WoundsBlock header so the always-visible
// sheet stays uncluttered:
//
//   * base (Healthy level)  -- Healthy = Earth × base   (default 5)
//   * per-rank multiplier   -- each later level adds Earth × mult (default 2)
//
// Both are campaign settings, not in-session mutations, so this is a form:
// the steppers drive LOCAL state and nothing is committed until Accept
// (Cancel therefore reverts). On accept the values route through
// appCtrl.setBaseHealthMultiplier / setHealthMultiplier so the dirty flag
// + narrow wounds_changed signal stay correct. Opened from the WoundsBlock
// header gear:
//     healthLevelsDlg.present()
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 420, 420)
    padding: Theme.s5

    // RAW defaults (L5R 4e core).
    readonly property int _defBase: 5
    readonly property int _defMult: 2

    // --- local (uncommitted) state --------------------------------
    property int _base: _defBase
    property int _mult: _defMult

    readonly property int _earth: pcProxy && pcProxy.rings ? (pcProxy.rings.earth || 0) : 0

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "体"
    accent: Theme.accent
    accentDark: Theme.accentMuted
    title: qsTr("Health Levels")
    tagline: qsTr("how the body's endurance is measured")
    acceptText: qsTr("Apply")
    acceptGlyph: "体"
    statusText: qsTr("Healthy = Earth × %1   ·   later levels add Earth × %2").arg(root._base).arg(root._mult)
    onAccepted: {
        if (!appCtrl)
            return;
        appCtrl.setBaseHealthMultiplier(root._base);
        appCtrl.setHealthMultiplier(root._mult);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        root._base = pcProxy ? pcProxy.baseHealthMultiplier : root._defBase;
        root._mult = pcProxy ? pcProxy.healthMultiplier : root._defMult;
        root.open();
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: Theme.s4

        // ---- base (Healthy level) --------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s3

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    text: qsTr("HEALTHY LEVEL")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.4
                    color: Theme.heading
                }
                Label {
                    text: qsTr("Earth × %1 = %2").arg(root._base).arg(root._earth * root._base)
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }
            Widgets.RankStepper {
                value: root._base
                from: 1
                to: 20
                onValueModified: function (v) {
                    root._base = v;
                }
            }
        }

        // ---- per-rank multiplier ---------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s3

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    text: qsTr("LEVEL MULTIPLIER")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.4
                    color: Theme.heading
                }
                Label {
                    text: qsTr("each later level adds Earth × %1 = %2").arg(root._mult).arg(root._earth * root._mult)
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }
            Widgets.RankStepper {
                value: root._mult
                from: 1
                to: 10
                onValueModified: function (v) {
                    root._mult = v;
                }
            }
        }

        // ---- reset to default ------------------------------------
        Label {
            Layout.alignment: Qt.AlignRight
            visible: root._base !== root._defBase || root._mult !== root._defMult
            text: qsTr("reset to default")
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsCaption
            font.underline: resetMa.containsMouse
            color: Theme.accent
            MouseArea {
                id: resetMa
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    root._base = root._defBase;
                    root._mult = root._defMult;
                }
            }
        }
    }
}
