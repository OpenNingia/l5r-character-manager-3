// Copyright (C) 2014-2026 Daniele Simonetti
// AdvanceRankDialog -- QML-native rank-up gateway. Replaces the legacy
// QWidget NextRankDlg (l5r/dialogs/newrankdlg.py). Opened from the
// Character section's "Advance Rank" callout:
//     advanceRankDlg.present()
//
// Two ways forward at a rank boundary:
//   - PRIMARY "Advance": continue in the CURRENT school, or -- when on an
//     alternate path -- resume the FORMER school (leave_path). Calls
//     appCtrl.advanceRank(). On a path with no former school to return to,
//     `canContinue` is false and Advance is disabled.
//   - SECONDARY "Join a new school": multiclass -- enter a new/advanced
//     school or an alternate path. Closes this dialog and emits
//     requestJoinSchool(), which the Character section routes to
//     JoinSchoolDialog. Always offered (canJoinNewSchool), so the former
//     dead-end (path with no former school) now has a way out.
//
// Info shape (from appCtrl.advanceRankInfo()):
//   { nextRank, onPath, currentSchool, formerSchool, canContinue,
//     canJoinNewSchool }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // Emitted when the player chooses multiclass over advancing in place;
    // the host (CharacterSection) opens JoinSchoolDialog in response.
    signal requestJoinSchool

    // --- state ----------------------------------------------------
    property var _info: ({})
    readonly property bool _onPath: !!_info.onPath
    readonly property bool _canContinue: _info.canContinue === undefined ? true : !!_info.canContinue
    readonly property bool _canJoinNewSchool: _info.canJoinNewSchool === undefined ? true : !!_info.canJoinNewSchool
    readonly property int _nextRank: _info.nextRank || 0
    readonly property string _currentSchool: _info.currentSchool || ""
    readonly property string _formerSchool: _info.formerSchool || ""

    // --- size: a compact confirm, not the two-pane catalogue. Wide
    // enough that the secondary "join a new school" action sits beside
    // its heading without overflowing once the labels are translated
    // (e.g. the Italian button is ~2x the English width). -----
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 520, 520)
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
        return qsTr("You walk the path of %1. To rise further you must join a new school.").arg(dlg._currentSchool);
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

        // --- secondary path: multiclass -------------------------------
        // Joining a new school is a genuinely different choice from
        // advancing in place, so it gets its own affordance below a
        // hairline divider rather than crowding the footer's primary
        // Advance. In the dead-end case (a path with no former school)
        // this is the only way forward.
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: Theme.s2
            Layout.preferredHeight: 1
            visible: dlg._canJoinNewSchool
            color: Theme.divider
            opacity: Theme.dividerOpacity
        }
        RowLayout {
            Layout.fillWidth: true
            visible: dlg._canJoinNewSchool
            spacing: Theme.s3

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Walk a different path")
                    wrapMode: Text.WordWrap
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.0
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("enter a new school, an advanced school, or an alternate path")
                    wrapMode: Text.WordWrap
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }
            Widgets.L5RButton {
                text: qsTr("Join a new school")
                primary: false
                Layout.alignment: Qt.AlignVCenter
                onClicked: {
                    dlg.reject();
                    dlg.requestJoinSchool();
                }
            }
        }
    }
}
