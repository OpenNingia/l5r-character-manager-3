// Copyright (C) 2014-2026 Daniele Simonetti
// Kiho section (気 -- ki, "spirit / breath") -- replaces the kiho half of
// the legacy l5r/ui/tabs/powers.py. (The kata half is its own QML
// section, `kata`; tattoos -- which share kiho storage but are a distinct
// concept -- are the `tattoo` section.)
//
// Design intent: "The Scroll of Spirit." A kiho is a spiritual technique
// bound to one of the five elements; only those who walk a disciplined
// path -- Monks, Shugenja, Ninja -- may learn one, and only when their
// Ring (or School rank) runs deep enough, paying experience scaled to
// that path. So the page reads as a register of the disciplines the
// character has drawn through breath and spirit. Each kiho is a card
// stamped on the left with its MASTERY rank inside an element-coloured
// tile (the §2.3 ring palette is the primary visual hook here, exactly as
// in Kata), the kiho name as the title, an ELEMENT · TYPE small-caps
// subtitle, the XP paid on the right rail, and a hover-revealed remove
// handle. Click a card to expand its full description inline.
//
// Unlike techniques (granted by school rank), kiho are BOUGHT -- so the
// head of the panel carries a quiet gold "Learn a Kiho" affordance that
// opens BuyKihoDialog (a QML-native catalogue that gates each kiho on the
// character's path + Ring/School-rank tests).
//
// Data contract expected from the proxy (degrades gracefully to the
// empty-state when missing):
//   pcProxy.kiho: [
//     { id:           "the_touch_of_the_void",  // also keys removal
//       name:         "The Touch of the Void",
//       element:      "void",            // ring key -> Theme.ringColor
//       elementLabel: "Void",            // localised ring name
//       mastery:      3,
//       type:         "mystical",        // kiho kind, lower-cased key
//       typeLabel:    "Mystical",        // display label
//       cost:         6,                 // XP actually paid (0 if free)
//       description:  "…" },             // prose; may be ""
//     ...
//   ]
// Required controller methods on appCtrl:
//   buyKiho(id)
//   removeKiho(id)
//   availableKihoToBuy() -> [{ id, name, element, elementLabel, mastery,
//                              type, typeLabel, cost, description, source,
//                              path:{kind,met}, eligible, reason }]
//                           (consumed by the dialog)
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
    readonly property var _kiho: (pcProxy && pcProxy.kiho) ? pcProxy.kiho : []
    readonly property bool _hasKiho: _kiho.length > 0

    // Free kiho granted by a School rank (monks). When > 0 the next kiho
    // learned costs no XP -- announced here by a "N FREE" pill and honoured
    // by BuyKihoDialog / api.character.powers.buy_kiho. This is the
    // in-section landing for the TOC opportunity badge.
    readonly property int _freeKiho: (pcProxy && pcProxy.freeKihoCount) ? pcProxy.freeKihoCount : 0

    // Total XP committed to kiho -- the footer coda. Monk-granted kiho
    // can be free, so this is the sum actually paid, not a count.
    readonly property int _spentXp: {
        var n = 0;
        for (var i = 0; i < _kiho.length; ++i)
            n += (_kiho[i].cost || 0);
        return n;
    }

    // Id of the currently-expanded kiho, or "" for none. A single id
    // (not per-card toggles) so opening one collapses the previous,
    // keeping a long scroll compact while reading -- mirrors Kata.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    function _requestRemove(item) {
        if (!item || !appCtrl)
            return;
        appCtrl.removeKiho(item.id);
    }

    // -----------------------------------------------------------------
    // Inline kiho chooser -- replaces the legacy KihoDialog.
    // -----------------------------------------------------------------
    Dialogs.BuyKihoDialog {
        id: buyKihoDlg
    }

    // -----------------------------------------------------------------
    // The whole scroll lives on a single parchment SheetPanel. Being a
    // Pane, it forces ink-on-paper palette onto every descendant Label,
    // so the cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Kiho")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count + add affordance -------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("spiritual techniques drawn through breath and the five elements")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasKiho
                    text: section._kiho.length === 1 ? qsTr("1 kiho") : qsTr("%1 kiho").arg(section._kiho.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }

                // "N FREE" pill -- blessing-blue (the §6.16 positive-action
                // hue), set apart from the gold add button so the player
                // sees at a glance that learning a kiho now costs nothing.
                Rectangle {
                    visible: section._freeKiho > 0
                    Layout.alignment: Qt.AlignVCenter
                    implicitHeight: 20
                    implicitWidth: freePillLabel.implicitWidth + 16
                    radius: 10
                    color: Theme.secondary
                    Label {
                        id: freePillLabel
                        anchors.centerIn: parent
                        text: section._freeKiho === 1 ? qsTr("1 FREE") : qsTr("%1 FREE").arg(section._freeKiho)
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsMicro
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.2
                        color: Theme.whiteWash
                    }
                }

                // Gold-outlined add affordance -- ink-on-paper button,
                // same vocabulary as Skills' "+ New Skill" / Kata's
                // "Learn a Kata".
                Button {
                    id: learnKihoBtn
                    text: qsTr("＋  Learn a Kiho")
                    onClicked: buyKihoDlg.present()
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 14
                    rightPadding: 14

                    contentItem: Label {
                        text: learnKihoBtn.text
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.6
                        color: Theme.heading
                        opacity: learnKihoBtn.hovered ? 1.0 : 0.88
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        // Gold wash derived from the heading token (not a
                        // free hex) -- warms on hover, deepens on press.
                        color: learnKihoBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : learnKihoBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
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
                visible: !section._hasKiho
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "気"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.heading
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No kiho learned yet.")
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
                    text: qsTr("A kiho channels the elements through disciplined breath. Walk the path of a Monk, Shugenja, or Ninja, deepen the Ring it draws upon, then make the technique your own.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The scroll of disciplines ---------------------------
            Repeater {
                model: section._kiho
                delegate: KihoCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasKiho
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasKiho
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("%1 experience drawn through breath and spirit").arg(section._spentXp)
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
    // KihoCard -- one learned discipline. Defined inline (no reuse
    // outside this section). The card carries an element-coloured mastery
    // stamp on the left, the name + ELEMENT · TYPE subtitle in the middle,
    // the XP paid on the right rail, a hover-revealed remove handle, and
    // an inline description revealed on tap.
    // =================================================================
    component KihoCard: Rectangle {
        id: card
        property var item: null

        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed kiho)")
        readonly property string _elementKey: (item && item.element) ? item.element : "void"
        readonly property string _elementLabel: (item && item.elementLabel) ? item.elementLabel : ""
        readonly property string _typeLabel: (item && item.typeLabel) ? item.typeLabel : ""
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

        // Left rail accent -- the element-hued strip that ties the
        // discipline to the Ring it draws upon.
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

                // ---- Name + element · type subtitle -----------------
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
                    // ELEMENT · TYPE -- the element label is the primary
                    // ring-hued hook (matching Kata); the kiho kind follows
                    // it in a quieter ink so colour stays tied to the Ring.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Label {
                            visible: card._elementLabel.length > 0
                            text: card._elementLabel.toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.letterSpacing: 1.4
                            font.weight: Theme.wSemiBold
                            color: card._ringColor
                            opacity: 0.9
                        }
                        Label {
                            visible: card._elementLabel.length > 0 && card._typeLabel.length > 0
                            text: "·"
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.4
                        }
                        Label {
                            visible: card._typeLabel.length > 0
                            Layout.fillWidth: true
                            text: card._typeLabel.toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.letterSpacing: 1.4
                            font.weight: Theme.wSemiBold
                            color: Theme.ink
                            opacity: 0.55
                            elide: Text.ElideRight
                        }
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
                        ToolTip.text: qsTr("Unlearn this kiho")
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
