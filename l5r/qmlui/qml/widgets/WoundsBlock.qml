// Copyright (C) 2014-2026 Daniele Simonetti
// Full-width wounds panel: header + status banner + 4x2 card grid.
// Replaces the legacy right-column ladder. Reads `wounds`, `currentWounds`,
// `maxWounds`, `currentWoundLevel`, `healthMultiplier`, `rings` from
// pcProxy, and routes mutations through appCtrl.damageHealth /
// setWoundsTotal / resetWounds (so the dirty flag stays correct).
// Interactions:
//   * stepper [- N +]  -> appCtrl.damageHealth(+/-1)
//   * click card       -> appCtrl.setWoundsTotal(bucketStart) ; HEALTHY = 0
//   * shift+click card -> appCtrl.resetWounds() (heals to zero)
// A header tooltip carries the legend (cell layout / formula / interaction)
// so the visual chrome stays compact -- per the design pass that dropped
// the in-panel legend strip.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0
import ClanTheme 1.0

Pane {
    id: panel

    // pcProxy + appCtrl are root context properties injected by app.py.
    readonly property var _wounds: pcProxy ? pcProxy.wounds : []
    readonly property int _hm: pcProxy ? pcProxy.healthMultiplier : 2
    readonly property int _cur: pcProxy ? pcProxy.currentWounds : 0
    readonly property int _max: pcProxy ? pcProxy.maxWounds : 0
    readonly property int _lvl: pcProxy ? pcProxy.currentWoundLevel : 0
    readonly property var _rings: pcProxy ? pcProxy.rings : ({
            "earth": 0
        })

    // Parchment surface + ink-on-paper palette, identical to SheetPanel.
    background: Rectangle {
        color: ClanTheme.paper
        radius: 0
    }
    palette.windowText: Theme.ink
    palette.text: Theme.ink
    palette.buttonText: Theme.ink
    palette.base: Theme.parchmentBase
    palette.alternateBase: Theme.parchmentInset
    palette.placeholderText: Theme.inkFaint
    palette.mid: Theme.inkFaint

    padding: 12

    // ---------- helpers ----------------------------------------------
    function _nameFor(idx) {
        const names = [qsTr("Healthy"), qsTr("Nicked"), qsTr("Grazed"), qsTr("Hurt"), qsTr("Injured"), qsTr("Crippled"), qsTr("Down"), qsTr("Out")];
        return names[Math.max(0, Math.min(idx, 7))];
    }

    // Card background by level + active state. HEALTHY..CRIPPLED share
    // the parchment-inset cream; DOWN is permanently rose-tinted; OUT is
    // a deep crimson regardless of active state -- the rule mirrors the
    // mockup, so the two terminal cards "feel" ominous even at a glance.
    function _cardBg(idx, active) {
        if (idx === 7)
            return active ? "#4a1e16" : "#5a261c";
        if (idx === 6)
            return active ? "#d99090" : "#f0c8c8";
        if (active)
            return Theme.positive;
        return Theme.parchmentInset;
    }
    function _cardInk(idx, active) {
        if (idx === 7)
            return "#f6e6c8";
        if (idx === 6)
            return active ? "#3a0e0e" : "#5a1a1a";
        if (active)
            return Theme.parchmentBase;
        return Theme.ink;
    }
    function _bucketStart(idx) {
        if (idx <= 0 || !panel._wounds[idx - 1])
            return 0;
        return panel._wounds[idx - 1].value;
    }
    function _statusCaption() {
        if (panel._lvl >= 7)
            return qsTr("unconscious");
        if (panel._cur === 0)
            return qsTr("no wounds taken");
        const start = panel._bucketStart(panel._lvl);
        const end = panel._wounds[panel._lvl] ? panel._wounds[panel._lvl].value : panel._max;
        const inLvl = Math.max(0, panel._cur - start);
        const size = Math.max(0, end - start);
        const toNext = Math.max(0, end - panel._cur);
        return qsTr("%1 / %2 wounds at this level · %3 to next").arg(inLvl).arg(size).arg(toNext);
    }

    contentItem: ColumnLayout {
        spacing: 10

        // ---------- header row -----------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: "❖"
                color: Theme.heading
                opacity: 0.7
                font.family: Theme.fontDisplay
                font.pixelSize:Theme.fsBody 
            }
            Label {
                text: qsTr("WOUNDS")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsHeading1
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.5
                color: Theme.heading

                HoverHandler {
                    id: titleHover
                }
                ToolTip.visible: titleHover.hovered
                ToolTip.delay: 300
                ToolTip.text: qsTr("Cell layout: name · threshold · TN penalty · wounds in level\n" + "Formula: HEALTHY = Earth × 5; next levels add Earth × multiplier\n" + "Click a card to jump there · ± with the stepper · shift+click to reset")
            }
            Label {
                text: qsTr("Earth %1").arg(panel._rings.earth || 0)
                font.pixelSize: Theme.fsCaption
                opacity: 0.65
                Layout.leftMargin: 4
            }
            Item {
                Layout.fillWidth: true
            }

            // The two right-hand steppers use the same parchment-pill
            // RankStepper as the social-flag rows above -- one UI shape
            // for every "tweak a small integer" interaction on the sheet.
            // `multiplier` is rarely changed (it's a campaign setting,
            // not in-session damage), but having it inline beats hunting
            // through a Gear menu.
            Label {
                text: qsTr("multiplier")
                font.pixelSize: Theme.fsCaption
                opacity: 0.6
            }
            RankStepper {
                value: panel._hm
                from: 1
                to: 10
                onValueModified: function (v) {
                    if (appCtrl)
                        appCtrl.setHealthMultiplier(v);
                }
            }
            Item {
                Layout.preferredWidth: 8
            }
            Label {
                text: qsTr("current")
                font.pixelSize: Theme.fsCaption
                opacity: 0.6
            }
            RankStepper {
                value: panel._cur
                from: 0
                to: Math.max(0, panel._max)
                onValueModified: function (v) {
                    if (appCtrl)
                        appCtrl.setWoundsTotal(v);
                }
            }
        }

        // ---------- status banner --------------------------------
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentBase
            border.color: Theme.borderSubtle
            border.width: 1
            radius: 3
            implicitHeight: bannerRow.implicitHeight + 16

            RowLayout {
                id: bannerRow
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                Rectangle {
                    Layout.preferredWidth: 10
                    Layout.preferredHeight: 10
                    radius: 5
                    color: panel._cardBg(panel._lvl, true)
                }
                // Body font (not Cinzel) -- Cinzel reads anaemic at
                // small sizes regardless of weight, and this is the
                // most-glanced label on the panel.
                Label {
                    text: panel._nameFor(panel._lvl)
                    font.pixelSize:Theme.fsBody 
                    font.weight: Font.Bold
                    color: panel._lvl >= 6 ? Theme.accentMuted : (panel._lvl === 0 ? Theme.positive : Theme.heading)
                }
                Label {
                    text: (panel._wounds[panel._lvl] && panel._wounds[panel._lvl].penalty > 0) ? qsTr("· +%1 TN to all rolls").arg(panel._wounds[panel._lvl].penalty) : qsTr("· no penalty")
                    font.pixelSize: Theme.fsCaption
                    opacity: 0.85
                }
                Item {
                    Layout.preferredWidth: 8
                }
                Label {
                    text: panel._statusCaption()
                    font.pixelSize: Theme.fsCaption
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    text: panel._cur
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatMedium
                    font.weight: Theme.wMedium
                    font.features: Theme.tabularNumbers
                    color: Theme.heading
                }
                Label {
                    text: qsTr("/ %1").arg(panel._max)
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatSmall
                    font.features: Theme.tabularNumbers
                    opacity: 0.7
                }
                Label {
                    text: qsTr("TOTAL")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.letterSpacing: 1.5
                    color: Theme.heading
                    opacity: 0.7
                    Layout.leftMargin: 4
                }
            }
        }

        // ---------- 4 × 2 card grid ------------------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 4
            columnSpacing: 8
            rowSpacing: 8

            Repeater {
                model: panel._wounds
                delegate: Rectangle {
                    id: card
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    readonly property bool _active: index === panel._lvl
                    color: panel._cardBg(index, _active)
                    border.color: _active ? Theme.heading : Theme.borderSubtle
                    border.width: _active ? 2 : 1
                    radius: 3

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 1

                        Label {
                            text: panel._nameFor(index).toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.5
                            color: panel._cardInk(index, card._active)
                        }
                        Label {
                            text: modelData.value
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsStatMedium
                            font.weight: Theme.wMedium
                            font.features: Theme.tabularNumbers
                            color: panel._cardInk(index, card._active)
                        }
                        Item {
                            Layout.fillHeight: true
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: index === 7 ? qsTr("unconscious") : qsTr("+%1 TN").arg(modelData.penalty)
                                font.pixelSize: Theme.fsCaption
                                font.weight: Font.DemiBold
                                color: panel._cardInk(index, card._active)
                                opacity: 0.9
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            // Per-level wound increment, straight from
                            // api.rules.get_wounds_table() via the proxy.
                            // Shown on every card including OUT -- the
                            // bucket size is just as meaningful for the
                            // fatal level (it's the cushion between
                            // "Down" and "really out").
                            Label {
                                text: qsTr("+%1").arg(modelData.inc)
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsStatSmall
                                font.features: Theme.tabularNumbers
                                color: panel._cardInk(index, card._active)
                                opacity: 0.75
                            }
                        }
                    }

                    HoverHandler {
                        id: cardHover
                        cursorShape: Qt.PointingHandCursor
                    }
                    // The hover overlay reuses the active fill at low
                    // alpha so the user can preview the destination
                    // tint before committing.
                    Rectangle {
                        anchors.fill: parent
                        radius: 3
                        color: panel._cardBg(index, true)
                        opacity: cardHover.hovered && !card._active ? 0.15 : 0
                        Behavior on opacity  {
                            NumberAnimation {
                                duration: 80
                            }
                        }
                    }
                    TapHandler {
                        acceptedButtons: Qt.LeftButton
                        onTapped: eventPoint => {
                            if (!appCtrl)
                                return;
                            if (eventPoint.modifiers & Qt.ShiftModifier) {
                                appCtrl.resetWounds();
                                return;
                            }
                            // Click jumps to the *start* of this level
                            // (so the card grid feels like a milestone
                            // selector, not a damage dial). HEALTHY -> 0.
                            const start = panel._bucketStart(index);
                            appCtrl.setWoundsTotal(start === 0 ? 0 : start + 1);
                        }
                    }
                }
            }
        }
    }
}
