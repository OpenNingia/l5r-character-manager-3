// Copyright (C) 2014-2026 Daniele Simonetti
// JoinSchoolDialog -- QML-native multiclass picker. Replaces the legacy
// QWidget SchoolChooserDialog (l5r/widgets/schoolchooser.py), the "Join a
// new school" branch of the rank-up flow. Opened from AdvanceRankDialog's
// secondary action via the Character section:
//     joinSchoolDlg.present()
//
// UX departs from the legacy three-checkbox filter: the player chooses the
// CATEGORY up front (new / advanced / alternate path), then a clan + a
// school filtered to that bucket. Hard requirements are shown read-only
// with ✓/✕ and BLOCK Accept until met; role-play ('more') requirements are
// toggles the player ticks to acknowledge. The optional "Multiple Schools"
// advantage may be bought alongside (soft XP note, never blocks -- the
// house-rules-friendly stance the QML UI takes elsewhere).
//
// Reads from appCtrl:
//   schoolsForJoin(clanId, category) -> [ _school_record ]  (id, name,
//        clanId, trait, book, page)
//   schoolRequirements(schoolId)     -> [ {text, rolePlay, satisfied} ]
//   multipleSchoolsInfo()            -> {cost, affordable}
//   clansList(), currentClanId()
// On accept: appCtrl.joinNewSchool(schoolId, buyMultipleSchools).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: 600
    padding: Theme.s5

    // --- chrome (via L5RDialog) -----------------------------------
    // Blue accent + 流 (ryū, school/style) keeps the whole advancement
    // flow in the opportunity-surface colour language shared with the
    // Character callout and AdvanceRankDialog.
    title: qsTr("Join a New School")
    tagline: qsTr("choose where your training turns next")
    seal: "流"
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Join")
    acceptGlyph: "流"
    acceptEnabled: root._selectedSchoolId.length > 0 && root._hardOk && (root._rolePlayChecked >= root._rolePlayTotal)
    statusText: {
        if (!root._selectedSchoolId)
            return qsTr("Choose a school to join.");
        if (!root._hardOk)
            return qsTr("Some requirements are not met.");
        if (root._rolePlayChecked < root._rolePlayTotal)
            return qsTr("Confirm the role-playing requirements to continue.");
        if (root._buyMultipleSchools && !root._multipleInfo.affordable)
            return qsTr("Joins — but you cannot yet afford Multiple Schools.");
        return qsTr("Joins the school and grants its Rank 1 technique.");
    }
    onAccepted: {
        if (root._selectedSchoolId && appCtrl)
            appCtrl.joinNewSchool(root._selectedSchoolId, root._buyMultipleSchools);
    }

    // --- state ----------------------------------------------------
    property string _category: "base"   // "base" | "advanced" | "path"
    property string _selectedClanId: ""
    property string _selectedSchoolId: ""
    property var _schools: []
    property var _requirements: []       // [{text, rolePlay, satisfied}]
    property int _rolePlayTotal: 0
    property int _rolePlayChecked: 0
    property bool _buyMultipleSchools: false
    property var _multipleInfo: ({
            "cost": 0,
            "affordable": true
        })

    // Accept is gated on every HARD requirement being satisfied (the
    // role-play ones are counted separately via the toggles).
    readonly property bool _hardOk: {
        for (var i = 0; i < root._requirements.length; ++i) {
            var r = root._requirements[i];
            if (!r.rolePlay && !r.satisfied)
                return false;
        }
        return true;
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        root._category = "base";
        root._selectedClanId = appCtrl ? appCtrl.currentClanId() : "";
        root._selectedSchoolId = "";
        root._buyMultipleSchools = false;
        root._multipleInfo = appCtrl ? appCtrl.multipleSchoolsInfo() : {
            "cost": 0,
            "affordable": true
        };
        root._refreshSchools();
        root._syncClanCombo();
        root._selectFirstSchool();
        root._refreshRequirements();
        root.open();
    }

    function _refreshSchools() {
        root._schools = (appCtrl && appCtrl.schoolsForJoin) ? (appCtrl.schoolsForJoin(root._selectedClanId, root._category) || []) : [];
    }

    function _refreshRequirements() {
        var reqs = (appCtrl && root._selectedSchoolId) ? (appCtrl.schoolRequirements(root._selectedSchoolId) || []) : [];
        root._requirements = reqs;
        var total = 0;
        for (var i = 0; i < reqs.length; ++i) {
            if (reqs[i].rolePlay)
                total++;
        }
        root._rolePlayTotal = total;
        // The Repeater rebuilds its toggles (all unchecked) whenever the
        // requirements array changes, so the running count resets to 0.
        root._rolePlayChecked = 0;
    }

    function _selectFirstSchool() {
        root._selectedSchoolId = root._schools.length > 0 ? root._schools[0].id : "";
        schoolCombo.currentIndex = root._schools.length > 0 ? 0 : -1;
    }

    function _setCategory(cat) {
        if (root._category === cat)
            return;
        root._category = cat;
        root._refreshSchools();
        root._selectFirstSchool();
        root._refreshRequirements();
    }

    function _syncClanCombo() {
        var idx = 0;
        for (var i = 0; i < clanCombo.count; ++i) {
            if (clanCombo.model[i].id === root._selectedClanId) {
                idx = i;
                break;
            }
        }
        clanCombo.currentIndex = idx;
    }

    function _currentSchoolRecord() {
        for (var i = 0; i < root._schools.length; ++i) {
            if (root._schools[i].id === root._selectedSchoolId)
                return root._schools[i];
        }
        return null;
    }

    // --- body -----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: Theme.s4

        // ---- Category segmented control --------------------------
        // No dedicated segmented-control token exists; per the design
        // system the sanctioned shape is a row of L5RButtons where the
        // active one is filled (primary) and the rest are outlined
        // (secondary). `_category` is the single source of truth, so the
        // three are mutually exclusive without a ButtonGroup. Each button
        // sizes to its label (not equal fillWidth) and the Flow wraps to a
        // second line rather than clipping long translations -- e.g. the
        // Italian "Percorso alternativo" is far wider than "Alternate path".
        Flow {
            Layout.fillWidth: true
            spacing: Theme.s2
            Repeater {
                model: [{
                        "key": "base",
                        "label": qsTr("New school")
                    }, {
                        "key": "advanced",
                        "label": qsTr("Advanced school")
                    }, {
                        "key": "path",
                        "label": qsTr("Alternate path")
                    }]
                delegate: Widgets.L5RButton {
                    text: modelData.label
                    primary: root._category === modelData.key
                    accent: Theme.secondary
                    accentDark: Theme.secondaryDark
                    onClicked: root._setCategory(modelData.key)
                }
            }
        }

        // ---- Clan / school / source / bonus ----------------------
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: Theme.s3
            rowSpacing: Theme.s2

            Label {
                text: qsTr("Clan:")
                color: Theme.ink
            }
            Widgets.L5RComboBox {
                id: clanCombo
                Layout.fillWidth: true
                textRole: "name"
                accent: root.accent
                model: {
                    var clans = appCtrl ? appCtrl.clansList() : [];
                    return [{
                            "id": "",
                            "name": qsTr("No Clan")
                        }].concat(clans);
                }
                onActivated: function (index) {
                    var rec = clanCombo.model[index];
                    root._selectedClanId = rec ? rec.id : "";
                    root._refreshSchools();
                    root._selectFirstSchool();
                    root._refreshRequirements();
                }
            }

            Label {
                text: qsTr("School:")
                color: Theme.ink
            }
            Widgets.L5RComboBox {
                id: schoolCombo
                Layout.fillWidth: true
                textRole: "name"
                accent: root.accent
                model: root._schools
                onActivated: function (index) {
                    var rec = root._schools[index];
                    root._selectedSchoolId = rec ? rec.id : "";
                    root._refreshRequirements();
                }
            }

            Label {
                text: qsTr("Source:")
                color: Theme.ink
            }
            Label {
                Layout.fillWidth: true
                font.italic: true
                color: Theme.inkMuted
                text: {
                    var rec = root._currentSchoolRecord();
                    if (!rec || !rec.book)
                        return "";
                    return rec.page ? qsTr("%1, page %2").arg(rec.book).arg(rec.page) : rec.book;
                }
            }

            Rectangle {
                Layout.columnSpan: 2
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.divider
                opacity: Theme.dividerOpacity
            }

            Label {
                text: qsTr("Bonus:")
                color: Theme.ink
            }
            Label {
                Layout.fillWidth: true
                color: {
                    var rec = root._currentSchoolRecord();
                    return rec && rec.trait ? Theme.positive : Theme.negative;
                }
                text: {
                    var rec = root._currentSchoolRecord();
                    return rec && rec.trait ? qsTr("+1 %1").arg(rec.trait) : qsTr("None");
                }
            }
        }

        // ---- Requirements checklist ------------------------------
        // Hard requirements are read-only ✓/✕ and block Accept; role-play
        // ('more') requirements are toggles the player ticks to confirm.
        ColumnLayout {
            Layout.fillWidth: true
            visible: root._requirements.length > 0
            spacing: Theme.s2

            Label {
                text: qsTr("Requirements")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsLabel
                font.weight: Theme.wSemiBold
                font.letterSpacing: 1.4
                color: Theme.heading
            }

            Repeater {
                model: root._requirements
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s2

                    // Leading status glyph (the BuyKata/Kiho/Spell
                    // convention): ✓ met / ✕ unmet for hard requirements,
                    // a neutral ◇ for role-play ones (which the toggle on
                    // the right is the actual gate for).
                    Label {
                        Layout.preferredWidth: 14
                        horizontalAlignment: Text.AlignHCenter
                        text: modelData.rolePlay ? "◇" : (modelData.satisfied ? "✓" : "✕")
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.wSemiBold
                        color: modelData.rolePlay ? Theme.inkMuted : (modelData.satisfied ? Theme.positive : Theme.negative)
                    }
                    Label {
                        Layout.fillWidth: true
                        text: modelData.text
                        wrapMode: Text.WordWrap
                        font.pixelSize: Theme.fsBody
                        font.italic: modelData.rolePlay
                        color: Theme.ink
                        opacity: (modelData.rolePlay || modelData.satisfied) ? 0.85 : 1.0
                    }
                    Widgets.L5RToggle {
                        visible: modelData.rolePlay
                        Layout.alignment: Qt.AlignVCenter
                        onToggled: root._rolePlayChecked += (checked ? 1 : -1)
                    }
                }
            }
        }

        // ---- Optional "Multiple Schools" advantage ---------------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.divider
            opacity: Theme.dividerOpacity
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s2

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    text: qsTr("Buy the “Multiple Schools” advantage")
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                }
                Label {
                    readonly property bool _short: root._buyMultipleSchools && !root._multipleInfo.affordable
                    text: _short ? qsTr("not enough XP — costs %1").arg(root._multipleInfo.cost) : qsTr("costs %1 XP").arg(root._multipleInfo.cost)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: _short ? Theme.negative : Theme.inkMuted
                }
            }
            Widgets.L5RToggle {
                checked: root._buyMultipleSchools
                Layout.alignment: Qt.AlignVCenter
                onToggled: root._buyMultipleSchools = checked
            }
        }
    }
}
