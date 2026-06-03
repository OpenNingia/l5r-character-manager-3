// Copyright (C) 2014-2026 Daniele Simonetti
// Techniques section (流 -- ryū, "school / flow") -- replaces the tech
// half of l5r/ui/tabs/techniques.py. (The spell half is its own QML
// section, `spells`, per the QML tab taxonomy.)
//
// Design intent: "The Path of the School." A character does not BUY
// techniques -- one is granted at each insight rank as the school's
// secrets open to them. So this section is read-only: it reads as an
// ascending ladder of named techniques, one rung per insight rank, the
// way a sensei's scroll would record a student's progress. Each rung is
// a card stamped on the left with the INSIGHT RANK at which it was
// earned (a filled clan-accent tile, white numeral -- the §6.15 kanji-
// tile vocabulary), the technique name as the card title, the school it
// belongs to as the subtitle, and a "School Rank N" pill on the right
// (the technique's own rank within that school). Click a card to expand
// its full description inline -- replacing the legacy double-click-for-
// description-dialog with at-the-table readability.
//
// There is intentionally no add/remove affordance: techniques follow
// from school-rank advancement, which happens on the Advancements
// section. An italic header note says as much so the absence reads as
// "earned, not bought" rather than "not yet implemented".
//
// Data contract expected from the proxy (degrades gracefully to the
// empty-state when missing):
//   pcProxy.techniques: [
//     { id:          "kakita-bushi-1",   // tech slug
//       name:        "The Way of the Crane",
//       schoolName:  "Kakita Bushi",
//       schoolId:    "kakita_bushi_school",
//       insightRank: 1,                   // char insight rank it was gained at
//       techRank:    1,                   // the tech's rank within its school
//       description: "…" },               // prose; may be ""
//     ...
//   ]
// Clan accent is read from the ClanTheme singleton (design system §5);
// MainSheet keeps it in sync with the active character's clan.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import Theme 1.0
import ClanTheme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // -----------------------------------------------------------------
    // Defensive binding -- proxy may be absent on first paint or under
    // the offscreen preview tool (which binds a null pcProxy).
    // -----------------------------------------------------------------
    readonly property var _techniques: (pcProxy && pcProxy.techniques) ? pcProxy.techniques : []
    readonly property bool _hasTechniques: _techniques.length > 0

    // Insight rank is the natural reading order for a progression ladder;
    // the proxy already emits them in order, but sort defensively so a
    // future multi-school projection can append out of order safely.
    readonly property var _ordered: {
        var arr = _techniques.slice();
        arr.sort(function (a, b) {
            return (a.insightRank || 0) - (b.insightRank || 0);
        });
        return arr;
    }

    // Id of the currently-expanded technique, or "" for none. A single
    // id (not per-card toggles) so opening one collapses the previous,
    // keeping a long path compact while reading -- mirrors SkillsSection.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    // -----------------------------------------------------------------
    // The whole path lives on a single parchment SheetPanel. Being a
    // Pane, it forces ink-on-paper palette onto every descendant Label,
    // so the cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Techniques")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count chip -------------------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("the secrets your school reveals as you advance")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasTechniques
                    text: section._techniques.length === 1 ? qsTr("1 technique") : qsTr("%1 techniques").arg(section._techniques.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            // ---- Empty state -----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                Layout.topMargin: 4
                visible: !section._hasTechniques
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "流"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: ClanTheme.primary
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No techniques learned yet.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Join a school and advance through its ranks — its techniques are granted to you one rung at a time.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The ladder of techniques ----------------------------
            Repeater {
                model: section._ordered
                delegate: TechCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasTechniques
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasTechniques
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("%1 rungs walked upon the path").arg(section._techniques.length)
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.letterSpacing: 2.0
                color: Theme.heading
                opacity: 0.70
            }
        }
    }

    // =================================================================
    // TechCard -- one rung of the path. Defined inline (no reuse outside
    // this section). The card carries an insight-rank stamp on the left,
    // the name + school subtitle in the middle, a school-rank pill on the
    // right, and an inline description revealed on tap.
    // =================================================================
    component TechCard: Rectangle {
        id: card
        property var item: null

        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed technique)")
        readonly property string _school: (item && item.schoolName) ? item.schoolName : ""
        readonly property int _insightRank: (item && item.insightRank) ? item.insightRank : 0
        readonly property int _techRank: (item && item.techRank) ? item.techRank : 0
        readonly property string _desc: (item && item.description) ? item.description : ""
        readonly property bool _hasDesc: _desc.length > 0
        readonly property bool _expanded: !!(item && section._expandedId === item.id)

        implicitHeight: cardBody.implicitHeight + 18

        color: cardHover.hovered || _expanded ? Theme.parchmentBase : Theme.parchmentInset
        border.color: cardHover.hovered || _expanded ? Qt.darker(ClanTheme.primary, 1.3) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: 120
            }
        }

        // Left rail accent -- the clan-hued strip that ties the rung to
        // the character's school identity.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: ClanTheme.primary
            opacity: 0.9
        }

        HoverHandler {
            id: cardHover
            cursorShape: card._hasDesc ? Qt.PointingHandCursor : Qt.ArrowCursor
        }
        // Whole-card tap toggles the description (only meaningful when
        // there is one to show).
        TapHandler {
            enabled: card._hasDesc
            onTapped: section._toggleExpand(card.item.id)
        }

        ColumnLayout {
            id: cardBody
            anchors.fill: parent
            anchors.margins: 9
            anchors.leftMargin: 13
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                // ---- Insight-rank stamp -- the rung number -----------
                // Filled clan-accent tile with a white numeral; the
                // §6.15 kanji-tile vocabulary repurposed as a progress
                // stamp. The tiny caption above keeps colour from being
                // the only carrier of meaning (§11).
                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("INSIGHT")
                        font.family: Theme.fontDisplay
                        font.pixelSize: 8
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.5
                        color: ClanTheme.primary
                        opacity: 0.75
                    }
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 38
                        implicitHeight: 38
                        radius: 4
                        color: ClanTheme.primary
                        Label {
                            anchors.centerIn: parent
                            text: card._insightRank > 0 ? card._insightRank : "–"
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsStatMedium
                            font.weight: Theme.wMedium
                            font.features: Theme.tabularNumbers
                            color: Theme.whiteWash
                        }
                    }
                }

                // ---- Name + school subtitle --------------------------
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 2

                    Label {
                        Layout.fillWidth: true
                        text: card._name
                        // Body face, regular weight, slightly enlarged --
                        // a proper-name title carries by size, not by a
                        // faux-bold of the single-weight body face (§3.4).
                        font.pixelSize: Theme.fsBody + 3
                        font.weight: Theme.wRegular
                        color: Theme.ink
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        visible: card._school.length > 0
                        Layout.fillWidth: true
                        text: card._school
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.6
                        elide: Text.ElideRight
                    }
                }

                // ---- School-rank pill --------------------------------
                // Outlined clan-accent pill (the PerkCard pill vocabulary)
                // -- the technique's own rank inside its school.
                Rectangle {
                    visible: card._techRank > 0
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredHeight: 18
                    implicitWidth: rankPill.implicitWidth + 14
                    color: "transparent"
                    border.color: ClanTheme.primary
                    border.width: 1
                    radius: 9
                    opacity: 0.8
                    Label {
                        id: rankPill
                        anchors.centerIn: parent
                        text: qsTr("School Rank %1").arg(card._techRank)
                        font.family: Theme.fontDisplay
                        font.pixelSize: 10
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.2
                        color: ClanTheme.primary
                    }
                }

                // ---- Expand chevron ----------------------------------
                Label {
                    visible: card._hasDesc
                    Layout.alignment: Qt.AlignVCenter
                    text: card._expanded ? "▲" : "▼"   // ▲ / ▼
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }
            }

            // ---- Expanded description -------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                visible: card._expanded && card._hasDesc
                spacing: 4

                Rectangle {
                    Layout.fillWidth: true
                    Layout.leftMargin: 50
                    Layout.preferredHeight: 1
                    color: ClanTheme.primary
                    opacity: 0.25
                }
                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 50
                    Layout.bottomMargin: 2
                    text: card._desc
                    textFormat: Text.PlainText
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                    opacity: 0.92
                }
            }
        }
    }
}
