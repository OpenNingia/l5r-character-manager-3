// Copyright (C) 2014-2026 Daniele Simonetti
// AdvanceRankDialog -- QML-native confirm for advancing Insight Rank.
// Replaces the "go on" branch of the legacy QWidget NextRankDlg
// (l5r/dialogs/newrankdlg.py). Opened from the Character section's
// "Advance Rank" callout:
//     advanceRankDlg.present()
//
// Scope (deliberately minimal, per the porting decision): this confirms
// advancing in the CURRENT school, or -- when the character is on an
// alternate path -- resuming the FORMER school (leave_path). Multiclass
// ("join a new school", rankadv.join_new) is a separate, larger port and
// is NOT offered here; when the only way forward is to join a new school
// (on a path with no former school to return to), `canContinue` is false
// and the dialog explains that rather than offering a dead Advance.
//
// Info shape (from appCtrl.advanceRankInfo()):
//   { nextRank, onPath, currentSchool, formerSchool, canContinue }
// On accept the dialog calls appCtrl.advanceRank().
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property var _info: ({})
    readonly property bool _onPath: !!_info.onPath
    readonly property bool _canContinue: _info.canContinue === undefined ? true : !!_info.canContinue
    readonly property int _nextRank: _info.nextRank || 0
    readonly property string _currentSchool: _info.currentSchool || ""
    readonly property string _formerSchool: _info.formerSchool || ""

    // --- size: a compact confirm, not the two-pane catalogue -----
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 460, 460)
    padding: Theme.s5

    // --- chrome (via L5RDialog) -----------------------------------
    // Blue (the opportunity-surface accent shared with the Character
    // callout and the §6.16 banner) keeps the whole "you unlocked
    // something" flow in one colour language. 道 (dō, "the way") is the
    // path-advancement seal, matching the Advancements §7 kanji.
    seal: "道"
    title: qsTr("Advance Rank")
    tagline: qsTr("a new rank opens the way forward")
    accent: Theme.secondary
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Advance")
    acceptGlyph: "道"
    acceptEnabled: dlg._canContinue
    statusText: dlg._canContinue ? "" : qsTr("Advancing from this path means joining a new school — not available here yet.")
    onAccepted: if (appCtrl)
        appCtrl.advanceRank()

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._info = (appCtrl && appCtrl.advanceRankInfo) ? (appCtrl.advanceRankInfo() || {}) : {};
        dlg.open();
    }

    function _bodyText() {
        if (!dlg._onPath)
            return qsTr("You may continue your training as a %1, rising to Insight Rank %2.").arg(dlg._currentSchool).arg(dlg._nextRank);
        if (dlg._canContinue)
            return qsTr("You may leave the path of %1 and resume %2, rising to Insight Rank %3.").arg(dlg._currentSchool).arg(dlg._formerSchool).arg(dlg._nextRank);
        return qsTr("You walk the path of %1. Advancing from here means joining a new school.").arg(dlg._currentSchool);
    }

    contentItem: ColumnLayout {
        spacing: Theme.s3

        Label {
            Layout.fillWidth: true
            text: dlg._bodyText()
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }
        Label {
            Layout.fillWidth: true
            visible: dlg._canContinue
            text: qsTr("Its blessings — a new technique, and perhaps spells or kiho — follow once you decide.")
            wrapMode: Text.WordWrap
            font.italic: true
            font.pixelSize: Theme.fsCaption
            color: Theme.ink
            opacity: 0.7
        }
    }
}
