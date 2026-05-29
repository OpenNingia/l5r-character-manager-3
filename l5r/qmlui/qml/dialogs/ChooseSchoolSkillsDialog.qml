// Copyright (C) 2014-2026 Daniele Simonetti
// ChooseSchoolSkillsDialog -- QML-native picker for the school-granted
// wildcard skills a character receives on joining their FIRST school (the
// datapack's <PlayerChoose>, parsed into school.skills_pc and copied onto
// the rank-1 advancement as rank_.skills_to_choose). Replaces the legacy
// QWidget SelWcSkills (l5r/dialogs/advdlg.py) without reusing it; opened
// from the Skills section's "Choose Skills" callout:
//     chooseSchoolSkillsDlg.present()
//
// Each wildcard set becomes one labelled dropdown of the concrete,
// still-unowned skills that satisfy it; each emphasis-to-choose becomes a
// labelled text field. On accept the dialog hands the resolved picks to
// appCtrl.applySchoolSkillChoices(...), which grants them and clears the
// pending list. Blue accent + 技 seal keep it in the same "you unlocked
// something" language as the rank-up / free-kiho surfaces.
//
// Data shape (from appCtrl.schoolSkillChoices()):
//   { skills:   [{ label: string, rank: int,
//                  options: [{ id, name }, ...] }, ...],
//     emphases: [{ skillId, skillName }, ...] }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    closePolicy: Popup.CloseOnEscape
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 520, 520)
    padding: Theme.s5

    // --- chrome (blue, the shared opportunity-surface accent) ----------
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    seal: "技"   // gi -- "skill / technique", the Skills section kanji
    title: qsTr("Choose School Skills")
    tagline: qsTr("your school grants you the choice of certain skills")
    acceptText: qsTr("Confirm")
    acceptGlyph: "技"
    acceptEnabled: root._ready()
    statusText: root._statusHint()
    onAccepted: if (appCtrl)
        appCtrl.applySchoolSkillChoices(root._skillPicks, root._emphPicks)

    // --- state ---------------------------------------------------------
    // _data mirrors appCtrl.schoolSkillChoices(). _skillPicks / _emphPicks
    // are the live selections, kept index-aligned to _data.skills /
    // _data.emphases. They are reassigned wholesale on every change so the
    // acceptEnabled / statusText bindings re-evaluate (QML does not track
    // in-place mutation of array elements).
    property var _data: ({})
    property var _skillPicks: []   // [{ id, rank }]
    property var _emphPicks: []    // [{ skillId, text }]

    readonly property var _skillSets: (_data && _data.skills) ? _data.skills : []
    readonly property var _emphSets: (_data && _data.emphases) ? _data.emphases : []
    readonly property bool _empty: _skillSets.length === 0 && _emphSets.length === 0

    // --- entrypoint ----------------------------------------------------
    function present() {
        root._data = (appCtrl && appCtrl.schoolSkillChoices) ? (appCtrl.schoolSkillChoices() || {}) : {};
        root._initPicks();
        root.open();
    }

    // Default each set to its first option (a populated dropdown shows
    // index 0 anyway -- mirrors the legacy combobox default) and each
    // emphasis to empty text.
    function _initPicks() {
        var sp = [];
        for (var i = 0; i < root._skillSets.length; ++i) {
            var opts = root._skillSets[i].options || [];
            sp.push({
                "id": opts.length > 0 ? opts[0].id : "",
                "rank": root._skillSets[i].rank
            });
        }
        root._skillPicks = sp;

        var ep = [];
        for (var j = 0; j < root._emphSets.length; ++j)
            ep.push({
                "skillId": root._emphSets[j].skillId,
                "text": ""
            });
        root._emphPicks = ep;
    }

    function _setSkillPick(setIndex, rec, rank) {
        var copy = root._skillPicks.slice();
        copy[setIndex] = {
            "id": rec ? rec.id : "",
            "rank": rank
        };
        root._skillPicks = copy;
    }

    function _setEmphText(setIndex, skillId, txt) {
        var copy = root._emphPicks.slice();
        copy[setIndex] = {
            "skillId": skillId,
            "text": txt
        };
        root._emphPicks = copy;
    }

    // Every set chosen, no skill picked twice, every emphasis named.
    function _ready() {
        var ids = [];
        for (var i = 0; i < root._skillPicks.length; ++i) {
            var id = root._skillPicks[i].id;
            if (!id)
                return false;
            if (ids.indexOf(id) !== -1)
                return false;
            ids.push(id);
        }
        for (var j = 0; j < root._emphPicks.length; ++j) {
            var t = root._emphPicks[j].text || "";
            if (t.trim().length === 0)
                return false;
        }
        return true;
    }

    // Footer recap -- explains the most relevant blocker, otherwise the
    // rulebook's "choose with care" caution.
    function _statusHint() {
        var ids = [];
        for (var i = 0; i < root._skillPicks.length; ++i) {
            var id = root._skillPicks[i].id;
            if (id && ids.indexOf(id) !== -1)
                return qsTr("You can't choose the same skill twice.");
            if (id)
                ids.push(id);
        }
        return qsTr("Choose with care — these become your school skills.");
    }

    // --- body ----------------------------------------------------------
    contentItem: ColumnLayout {
        spacing: Theme.s4

        // Empty-state guard (only if opened with nothing pending).
        Label {
            visible: root._empty
            Layout.fillWidth: true
            Layout.topMargin: Theme.s3
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("There are no school skills left to choose.")
            font.italic: true
            font.pixelSize: Theme.fsBody
            color: Theme.ink
            opacity: 0.7
        }

        // ---- One labelled dropdown per wildcard set -------------------
        Repeater {
            model: root._skillSets
            delegate: ColumnLayout {
                Layout.fillWidth: true
                spacing: 5

                required property int index
                required property var modelData
                readonly property var _options: modelData.options || []

                Label {
                    Layout.fillWidth: true
                    text: modelData.label
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsBody
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 0.6
                    color: Theme.heading
                    wrapMode: Text.WordWrap
                }

                Widgets.L5RComboBox {
                    Layout.fillWidth: true
                    visible: _options.length > 0
                    textRole: "name"
                    model: _options
                    accent: root.accent
                    currentIndex: _options.length > 0 ? 0 : -1
                    onActivated: function (optIdx) {
                        root._setSkillPick(index, _options[optIdx], modelData.rank);
                    }
                }

                // Rare dead-end: the character already owns every skill
                // matching this set. Mirrors the legacy empty-combobox
                // state -- accept stays disabled.
                Label {
                    visible: _options.length === 0
                    Layout.fillWidth: true
                    text: qsTr("No eligible skills remain for this choice.")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }
        }

        // ---- One labelled field per emphasis-to-choose ----------------
        Repeater {
            model: root._emphSets
            delegate: ColumnLayout {
                Layout.fillWidth: true
                spacing: 5

                required property int index
                required property var modelData

                Label {
                    Layout.fillWidth: true
                    text: qsTr("%1 — choose an emphasis").arg(modelData.skillName)
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsBody
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 0.6
                    color: Theme.heading
                    wrapMode: Text.WordWrap
                }

                // Parchment-skinned field (matches L5RComboBox chrome):
                // explicit ink/placeholder colours so it stays legible in
                // the Overlay layer regardless of the OS palette.
                TextField {
                    Layout.fillWidth: true
                    placeholderText: qsTr("e.g. Katana, Falconry, Goblin…")
                    color: Theme.ink
                    placeholderTextColor: Theme.inkFaint
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsBody
                    leftPadding: 10
                    rightPadding: 10
                    onTextChanged: root._setEmphText(index, modelData.skillId, text)
                    background: Rectangle {
                        color: Theme.parchmentBase
                        border.color: parent.activeFocus ? root.accent : Theme.borderSubtle
                        border.width: 1
                        radius: 2
                    }
                }
            }
        }
    }
}
