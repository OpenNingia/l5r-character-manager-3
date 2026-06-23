// Copyright (C) 2014-2026 Daniele Simonetti
// Kata section (型 -- kata, "form") -- replaces the kata half of the
// legacy l5r/ui/tabs/powers.py. (The kiho half is its own QML section,
// `kiho`, per the QML tab taxonomy.)
//
// Design intent: "The Scroll of Forms." A kata is a memorised martial
// form bound to one of the five elements; a samurai learns it by paying
// experience equal to its mastery, but only once their Ring in that
// element runs deep enough. So the page reads as a scroll recording the
// forms the character has committed to muscle and memory. Each form is a
// card stamped on the left with its MASTERY rank inside an
// element-coloured tile (the §2.3 ring palette is the primary visual
// hook here, the same way Skills colours rows by their ring), the kata
// name as the title, the element as a small-caps subtitle, the XP paid
// on the right rail, and a hover-revealed remove handle. Click a card to
// expand its full description inline.
//
// Unlike techniques (granted by school rank), kata are BOUGHT -- so the
// head of the panel carries a quiet gold "Learn a Kata" affordance that
// opens BuyKataDialog (a QML-native catalogue that gates each kata on
// the rulebook's requirement + ring tests).
//
// Data contract expected from the proxy (degrades gracefully to the
// empty-state when missing):
//   pcProxy.kata: [
//     { id:           "the_iron_forest_style",  // also keys removal
//       name:         "The Iron Forest Style",
//       element:      "fire",              // ring key -> Theme.ringColor
//       elementLabel: "Fire",              // localised ring name
//       mastery:      3,
//       cost:         3,                   // XP actually paid
//       description:  "…" },               // prose; may be ""
//     ...
//   ]
// Required controller methods on appCtrl:
//   buyKata(id)
//   removeKata(id)
//   availableKataToBuy() -> [{ id, name, element, elementLabel, mastery,
//                              cost, description, source, requirements,
//                              ringNeed, eligible }]   (consumed by the dialog)
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // -----------------------------------------------------------------
    // Defensive binding -- proxy may be absent on first paint or under
    // the offscreen preview tool (which binds a null pcProxy).
    // -----------------------------------------------------------------
    readonly property var _kata: (pcProxy && pcProxy.kata) ? pcProxy.kata : []
    readonly property bool _hasKata: _kata.length > 0

    // Total XP committed to forms -- the footer coda.
    readonly property int _spentXp: {
        var n = 0;
        for (var i = 0; i < _kata.length; ++i)
            n += (_kata[i].cost || 0);
        return n;
    }

    // Id of the currently-expanded kata, or "" for none. A single id
    // (not per-card toggles) so opening one collapses the previous,
    // keeping a long scroll compact while reading -- mirrors Skills.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    function _requestRemove(item) {
        if (!item || !appCtrl)
            return;
        appCtrl.removeKata(item.id);
    }

    // -----------------------------------------------------------------
    // Inline kata chooser -- replaces the legacy KataDialog.
    // -----------------------------------------------------------------
    Dialogs.BuyKataDialog {
        id: buyKataDlg
    }

    // -----------------------------------------------------------------
    // The whole scroll lives on a single parchment SheetPanel. Being a
    // Pane, it forces ink-on-paper palette onto every descendant Label,
    // so the cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Kata")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count + add affordance -------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("martial forms learned, bound to the five elements")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasKata
                    text: section._kata.length === 1 ? qsTr("1 form") : qsTr("%1 forms").arg(section._kata.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }

                // Gold-outlined add affordance -- ink-on-paper button,
                // same vocabulary as Skills' "+ New Skill".
                Button {
                    id: learnKataBtn
                    text: qsTr("＋  Learn a Kata")
                    onClicked: buyKataDlg.present()
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 14
                    rightPadding: 14

                    contentItem: Label {
                        text: learnKataBtn.text
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.6
                        color: Theme.heading
                        opacity: learnKataBtn.hovered ? 1.0 : 0.88
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        // Gold wash derived from the heading token (not a
                        // free hex) -- warms on hover, deepens on press.
                        color: learnKataBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : learnKataBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
                        border.width: 1
                        border.color: Theme.heading
                        radius: 1
                    }
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
                visible: !section._hasKata
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "型"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.heading
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No kata learned yet.")
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
                    text: qsTr("A kata is a perfected form of movement. Deepen the Ring it draws upon, then commit the form to memory.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The scroll of forms ---------------------------------
            Repeater {
                model: section._kata
                delegate: KataCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasKata
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasKata
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("%1 experience committed to muscle and memory").arg(section._spentXp)
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.wSemiBold
                font.letterSpacing: 2.0
                color: Theme.heading
                opacity: 0.70
            }
        }
    }

    // =================================================================
    // KataCard -- one learned form. Defined inline (no reuse outside
    // this section). The card carries an element-coloured mastery stamp
    // on the left, the name + element subtitle in the middle, the XP
    // paid on the right rail, a hover-revealed remove handle, and an
    // inline description revealed on tap.
    // =================================================================
    component KataCard: Rectangle {
        id: card
        property var item: null

        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed kata)")
        readonly property string _elementKey: (item && item.element) ? item.element : "void"
        readonly property string _elementLabel: (item && item.elementLabel) ? item.elementLabel : ""
        readonly property color _ringColor: Theme.ringColor(_elementKey)
        readonly property int _mastery: (item && item.mastery) ? item.mastery : 0
        readonly property int _cost: (item && item.cost !== undefined) ? item.cost : 0
        readonly property string _desc: (item && item.description) ? item.description : ""
        readonly property bool _hasDesc: _desc.length > 0
        readonly property bool _expanded: !!(item && section._expandedId === item.id)

        implicitHeight: cardBody.implicitHeight + 18

        color: cardHover.hovered || _expanded ? Theme.parchmentBase : Theme.parchmentInset
        border.color: cardHover.hovered || _expanded ? Qt.darker(_ringColor, 1.3) : Theme.borderSubtle
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

        // Left rail accent -- the element-hued strip that ties the form
        // to the Ring it draws upon.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: card._ringColor
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

                // ---- Mastery stamp -- the element-coloured tile -----
                // Filled ring-accent tile with a white numeral; the
                // §6.15 kanji-tile vocabulary repurposed as a mastery
                // stamp. The tiny caption above keeps colour from being
                // the only carrier of meaning (§11).
                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("MASTERY")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsMicro
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.5
                        color: card._ringColor
                        opacity: 0.85
                    }
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 38
                        implicitHeight: 38
                        radius: 4
                        color: card._ringColor
                        Label {
                            anchors.centerIn: parent
                            text: card._mastery > 0 ? card._mastery : "–"
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsStatMedium
                            font.weight: Theme.wMedium
                            font.features: Theme.tabularNumbers
                            color: Theme.whiteWash
                        }
                    }
                }

                // ---- Name + element subtitle ------------------------
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
                        visible: card._elementLabel.length > 0
                        Layout.fillWidth: true
                        text: card._elementLabel.toUpperCase()
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption
                        font.letterSpacing: 1.4
                        font.weight: Theme.wSemiBold
                        color: card._ringColor
                        opacity: 0.9
                        elide: Text.ElideRight
                    }
                }

                // ---- XP-paid rail -----------------------------------
                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: 44
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: card._cost
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatMedium
                        font.weight: Theme.wMedium
                        font.features: Theme.tabularNumbers
                        horizontalAlignment: Text.AlignRight
                        color: Theme.heading
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("XP")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsMicro
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 2.0
                        horizontalAlignment: Text.AlignRight
                        color: Theme.heading
                        opacity: 0.8
                    }
                }

                // ---- Expand chevron ---------------------------------
                Label {
                    visible: card._hasDesc
                    Layout.alignment: Qt.AlignVCenter
                    text: card._expanded ? "▲" : "▼"
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }

                // ---- Remove handle -- hover-revealed crimson cross ---
                // Holder is fixed-width so the XP rail doesn't dance
                // horizontally as the affordance fades in.
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter

                    AbstractButton {
                        id: removeBtn
                        anchors.fill: parent
                        visible: cardHover.hovered || removeBtn.hovered
                        onClicked: section._requestRemove(card.item)

                        background: Rectangle {
                            radius: 11
                            color: removeBtn.hovered ? Theme.accent : "transparent"
                            border.color: Theme.accent
                            border.width: 1
                            opacity: removeBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✕"
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: removeBtn.hovered ? Theme.whiteWash : Theme.accent
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Unlearn this kata")
                    }
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
                    color: card._ringColor
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
