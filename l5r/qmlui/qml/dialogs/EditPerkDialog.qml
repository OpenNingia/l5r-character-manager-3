// Copyright (C) 2014-2026 Daniele Simonetti
// EditPerkDialog -- in-place editor for a previously-inscribed merit or
// flaw. Mirrors the legacy BuyPerkDialog edit mode: the rule and rank
// stay locked (changing those is semantically a remove+rebuy); only the
// per-instance notes (`extra`) and the XP figure are editable.
//     editDlg.present({
//         advId: "...", name: "Allies", category: "Social", rank: 2,
//         cost: 4, suggestedCost: 7, subtype: "Yasuki Trading",
//         kind: "merit"   // "merit" | "flaw"
//     })
// On accept, calls appCtrl.editPerk(advId, extra, overrideCost) where
// `overrideCost == -1` means "use the rulebook suggestion (with any
// applicable clan/tag discount)". Any non-negative value is manual.
// Built on Widgets.L5RDialog (shared header/footer/background); the body
// here is the read-only target plaque + notes field + price scroll.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 520, 520)
    padding: Theme.s5

    // --- target + edit state --------------------------------------
    property string kind: "merit"
    property string advId: ""
    property string perkName: ""
    property string perkCategory: ""
    property int perkRank: 1
    property int suggestedCost: 0
    property string _subtype: ""
    property bool _overrideOn: false
    property int _overrideCost: 0

    // --- derived ---------------------------------------------------
    readonly property bool _isFlaw: kind === "flaw"
    readonly property color _accent: _isFlaw ? Theme.accent : Theme.secondary
    readonly property string _seal: _isFlaw ? "業" : "縁"
    readonly property int _effectiveCost: _overrideOn ? _overrideCost : suggestedCost

    // --- chrome (via L5RDialog) -----------------------------------
    title: _isFlaw ? qsTr("Edit Burden") : qsTr("Edit Blessing")
    tagline: qsTr("notes and cost; the rule and rank are fixed")
    seal: _seal
    accent: _accent
    accentDark: _isFlaw ? Theme.accentMuted : Theme.secondaryDark
    acceptText: qsTr("Save")
    statusText: _isFlaw ? qsTr("This burden will grant +%1 XP.").arg(_effectiveCost) : qsTr("This blessing will require %1 XP.").arg(_effectiveCost)
    onAccepted: if (appCtrl && appCtrl.editPerk)
        appCtrl.editPerk(dlg.advId, dlg._subtype, dlg._overrideOn ? dlg._overrideCost : -1)

    // --- entrypoint -----------------------------------------------
    // `data` is a QVariantMap (or JS object) with the fields listed in
    // the header comment. Named `present` rather than `open` to avoid
    // shadowing Dialog's built-in open().
    function present(data) {
        if (!data)
            return;
        dlg.kind = data.kind || "merit";
        dlg.advId = data.advId || "";
        dlg.perkName = data.name || "";
        dlg.perkCategory = data.category || "";
        dlg.perkRank = data.rank || 1;
        dlg.suggestedCost = data.suggestedCost || 0;
        dlg._subtype = data.subtype || "";
        // Open in override mode only when the stored cost diverges from
        // the rulebook suggestion. A 0 XP suggestion is legitimate (clan
        // discounts make some merits free), so it no longer forces the
        // manual path -- the player can still flip the switch by hand.
        var current = data.cost || 0;
        dlg._overrideOn = current !== dlg.suggestedCost;
        dlg._overrideCost = current;
        dlg.open();
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: 12

        // ---- Target plaque -- read-only header that anchors the
        // editor to the perk being edited. Cinzel name + a quiet
        // "Social · Rank 2" caption.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: targetBody.implicitHeight + 16
            color: Theme.parchmentInset
            border.color: Theme.borderSubtle
            border.width: 1
            radius: 2

            RowLayout {
                id: targetBody
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: dlg.perkName
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsHeading1
                        font.weight: Theme.wSemiBold
                        color: Theme.ink
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: dlg.perkCategory.length > 0 || dlg.perkRank > 0
                        text: {
                            var parts = [];
                            if (dlg.perkCategory.length > 0)
                                parts.push(dlg.perkCategory);
                            if (dlg.perkRank > 0)
                                parts.push(qsTr("Rank %1").arg(dlg.perkRank));
                            return parts.join("  ·  ");
                        }
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.65
                    }
                }
            }
        }

        // ---- Notes -- the per-instance free-text (PerkAdv.extra).
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Label {
                text: qsTr("Notes")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
                Layout.preferredWidth: 90
            }
            TextField {
                id: subtypeField
                Layout.fillWidth: true
                text: dlg._subtype
                onTextEdited: dlg._subtype = text
                placeholderText: dlg._isFlaw ? qsTr("circumstance, target, or detail…") : qsTr("name, ally, or detail…")
                color: Theme.ink
                placeholderTextColor: Theme.inkFaint
                background: Rectangle {
                    color: Theme.parchmentBase
                    border.color: Theme.borderSubtle
                    border.width: 1
                    radius: 2
                }
            }
        }

        // ---- Price scroll -- same visual vocabulary as
        // InscribePerkDialog: suggested-plaque by default; flipping the
        // override switch swaps it for a crimson-rimmed inkwell SpinBox
        // seeded with the current value, with a "reset to N" chip when
        // the figure drifts from suggestion.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: priceBody.implicitHeight + 22

            color: dlg._overrideOn ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.05) : Theme.parchmentInset
            border.color: dlg._overrideOn ? Theme.accent : Theme.borderSubtle
            border.width: dlg._overrideOn ? 1.5 : 1
            radius: 2

            Behavior on color {
                ColorAnimation {
                    duration: 160
                }
            }
            Behavior on border.color {
                ColorAnimation {
                    duration: 160
                }
            }
            Behavior on border.width {
                NumberAnimation {
                    duration: 160
                }
            }

            ColumnLayout {
                id: priceBody
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            text: dlg._overrideOn ? qsTr("MANUAL COST") : qsTr("SUGGESTED BY THE RULEBOOK")
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 2.0
                            color: dlg._overrideOn ? Theme.accent : Theme.heading
                            opacity: 0.9
                        }
                        Label {
                            text: dlg._isFlaw ? qsTr("experience the gods will grant in return") : qsTr("experience the chronicle will require")
                            font.italic: true
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.6
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    Item {
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 52

                        // Suggested-cost plaque.
                        Rectangle {
                            anchors.fill: parent
                            visible: !dlg._overrideOn
                            color: Theme.parchmentBase
                            border.color: Theme.heading
                            border.width: 1
                            radius: 2
                            Label {
                                anchors.centerIn: parent
                                text: (dlg._isFlaw ? "+" : "") + dlg.suggestedCost
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsXpValue
                                font.weight: Theme.wSemiBold
                                font.features: Theme.tabularNumbers
                                color: dlg._isFlaw ? Theme.highlight : dlg._accent
                            }
                            Label {
                                anchors.bottom: parent.bottom
                                anchors.right: parent.right
                                anchors.bottomMargin: 4
                                anchors.rightMargin: 6
                                text: qsTr("XP")
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.headingWeight
                                font.letterSpacing: 2.0
                                color: dlg._isFlaw ? Theme.highlight : dlg._accent
                                opacity: 0.7
                            }
                        }

                        // Override-cost inkwell SpinBox.
                        SpinBox {
                            id: overrideSpin
                            anchors.fill: parent
                            visible: dlg._overrideOn
                            from: 0
                            to: 999
                            value: dlg._overrideCost
                            editable: true
                            onValueModified: dlg._overrideCost = value

                            background: Rectangle {
                                color: Theme.parchmentBase
                                border.color: Theme.accent
                                border.width: 1
                                radius: 2
                            }
                            contentItem: TextInput {
                                text: overrideSpin.textFromValue(overrideSpin.value, overrideSpin.locale)
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsXpValue
                                font.weight: Theme.wSemiBold
                                font.features: Theme.tabularNumbers
                                color: Theme.accent
                                horizontalAlignment: TextInput.AlignHCenter
                                verticalAlignment: TextInput.AlignVCenter
                                readOnly: !overrideSpin.editable
                                validator: overrideSpin.validator
                                inputMethodHints: Qt.ImhFormattedNumbersOnly
                                onTextEdited: {
                                    var v = parseInt(text);
                                    if (!isNaN(v)) {
                                        overrideSpin.value = v;
                                        dlg._overrideCost = v;
                                    }
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 2
                    spacing: 10

                    Switch {
                        id: overrideSwitch
                        checked: dlg._overrideOn
                        onToggled: {
                            dlg._overrideOn = checked;
                            if (checked && dlg._overrideCost === 0) {
                                dlg._overrideCost = dlg.suggestedCost;
                            }
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: dlg._overrideOn ? qsTr("Manual cost — agreed with your GM.") : qsTr("Override the suggested cost")
                        font.pixelSize: Theme.fsBody
                        font.italic: !dlg._overrideOn
                        color: dlg._overrideOn ? Theme.accent : Theme.ink
                        opacity: dlg._overrideOn ? 1.0 : 0.7
                        wrapMode: Text.WordWrap
                    }
                    AbstractButton {
                        id: resetBtn
                        visible: dlg._overrideOn && dlg._overrideCost !== dlg.suggestedCost
                        onClicked: {
                            dlg._overrideCost = dlg.suggestedCost;
                            overrideSpin.value = dlg.suggestedCost;
                        }
                        implicitHeight: 22
                        leftPadding: 8
                        rightPadding: 8
                        background: Rectangle {
                            radius: 11
                            color: resetBtn.hovered ? Theme.heading : "transparent"
                            border.color: Theme.heading
                            border.width: 1
                            opacity: resetBtn.hovered ? 0.9 : 0.6
                        }
                        contentItem: Label {
                            text: qsTr("reset to %1").arg(dlg.suggestedCost)
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsMicro
                            font.weight: Theme.wSemiBold
                            font.letterSpacing: 1.2
                            color: resetBtn.hovered ? Theme.parchmentBase : Theme.heading
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }
    }
}
