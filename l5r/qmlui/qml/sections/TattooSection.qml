// Copyright (C) 2014-2026 Daniele Simonetti
// Tattoo section (彫 -- chō, "to carve / engrave") -- the mystic marks
// of the Togashi Order. In the legacy UI tattoos shared the Powers tab
// with kiho (l5r/ui/tabs/powers.py); in the QML taxonomy they earn their
// own scroll, parallel to Kiho. They share storage with kiho (both are
// KihoAdv) but are mechanically distinct: free, no element, no mastery,
// no XP -- so none of the Kiho section's vocabulary (element rings, a
// mastery stamp, an XP rail) applies here.
//
// Design intent: "The Living Ink." A Togashi ise zumi bears tattoos
// carved into the flesh that wake to serve them -- so this page reads as
// a register of the marks the character carries. Each mark is a card
// stamped on the left with the 彫 seal inside a void-hued tile (the
// §6.15 kanji-tile vocabulary, here a carved sigil rather than a
// numeral), the tattoo name as the title, and a hover-revealed remove
// handle. Click a card to expand its full description inline. The seal's
// void/mystic purple is the section's own identity hue -- it is NOT an
// element label (tattoos carry no element); it sets these sacred marks
// apart from the elemental Kata and the spiritual Kiho.
//
// Tattoos are RECEIVED, not bought with experience -- so the head of the
// panel carries a quiet gold "Receive a Tattoo" affordance (the same
// add vocabulary as Skills / Kata) that opens BuyTattooDialog.
//
// Data contract expected from the proxy (degrades gracefully to the
// empty-state when missing):
//   pcProxy.tattoo: [
//     { id:          "the_dragons_breath_tattoo", // also keys removal
//       name:        "The Dragon's Breath",
//       description: "…" },                        // prose; may be ""
//     ...
//   ]
// Required controller methods on appCtrl:
//   buyTattoo(id)
//   removeTattoo(id)
//   availableTattooToBuy() -> [{ id, name, description, source }]
//                             (consumed by the dialog)
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // The void/mystic hue that gives tattoos their own dignity on the
    // sheet. Reused from the ring palette (an existing token, no inline
    // hex) for its sacred, otherworldly read -- never shown as an
    // element label, since a tattoo has no element.
    readonly property color _mark: Theme.ringVoid

    // -----------------------------------------------------------------
    // Defensive binding -- proxy may be absent on first paint or under
    // the offscreen preview tool (which binds a null pcProxy).
    // -----------------------------------------------------------------
    readonly property var _tattoo: (pcProxy && pcProxy.tattoo) ? pcProxy.tattoo : []
    readonly property bool _hasTattoo: _tattoo.length > 0

    // Id of the currently-expanded tattoo, or "" for none. A single id
    // (not per-card toggles) so opening one collapses the previous,
    // keeping a long scroll compact while reading -- mirrors Kata.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    function _requestRemove(item) {
        if (!item || !appCtrl)
            return;
        appCtrl.removeTattoo(item.id);
    }

    // -----------------------------------------------------------------
    // Inline tattoo chooser -- replaces the legacy TattooDialog.
    // -----------------------------------------------------------------
    Dialogs.BuyTattooDialog {
        id: buyTattooDlg
    }

    // -----------------------------------------------------------------
    // The whole register lives on a single parchment SheetPanel. Being a
    // Pane, it forces ink-on-paper palette onto every descendant Label,
    // so the cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Tattoos")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count + add affordance -------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("the living marks borne by the Togashi Order")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasTattoo
                    text: section._tattoo.length === 1 ? qsTr("1 mark") : qsTr("%1 marks").arg(section._tattoo.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }

                // Gold-outlined add affordance -- ink-on-paper button,
                // same vocabulary as Skills' "+ New Skill" / Kata's
                // "Learn a Kata".
                Button {
                    id: receiveTattooBtn
                    text: qsTr("＋  Receive a Tattoo")
                    onClicked: buyTattooDlg.present()
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 14
                    rightPadding: 14

                    contentItem: Label {
                        text: receiveTattooBtn.text
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.6
                        color: Theme.heading
                        opacity: receiveTattooBtn.hovered ? 1.0 : 0.88
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        // Gold wash derived from the heading token (not a
                        // free hex) -- warms on hover, deepens on press.
                        color: receiveTattooBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : receiveTattooBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
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
                visible: !section._hasTattoo
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "彫"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: section._mark
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No tattoos yet.")
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
                    text: qsTr("The ise zumi of the Togashi Order bear living tattoos that wake to serve them. Receive your first mark when your path allows it.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The register of marks -------------------------------
            Repeater {
                model: section._tattoo
                delegate: TattooCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasTattoo
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasTattoo
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: section._tattoo.length === 1 ? qsTr("one mark carved into living flesh") : qsTr("%1 marks carved into living flesh").arg(section._tattoo.length)
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
    // TattooCard -- one mark borne. Defined inline (no reuse outside
    // this section). The card carries the 彫 seal in a void-hued tile on
    // the left, the tattoo name in the middle, a hover-revealed remove
    // handle, and an inline description revealed on tap. There is no XP
    // rail: tattoos are free.
    // =================================================================
    component TattooCard: Rectangle {
        id: card
        property var item: null

        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed tattoo)")
        readonly property string _desc: (item && item.description) ? item.description : ""
        readonly property bool _hasDesc: _desc.length > 0
        readonly property bool _expanded: !!(item && section._expandedId === item.id)

        implicitHeight: cardBody.implicitHeight + 18

        color: cardHover.hovered || _expanded ? Theme.parchmentBase : Theme.parchmentInset
        border.color: cardHover.hovered || _expanded ? Qt.darker(section._mark, 1.3) : Theme.borderSubtle
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

        // Left rail accent -- the void-hued strip that marks the card as
        // one of the Togashi Order's sacred tattoos.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: section._mark
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

                // ---- Carved-seal stamp -- the void-hued tile ---------
                // Filled tile bearing the 彫 ("carve") seal -- the §6.15
                // kanji-tile vocabulary repurposed as a per-mark sigil.
                // The caption keeps the seal from being the only carrier
                // of meaning (§11) and names the concept plainly.
                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 1
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("MARK")
                        font.family: Theme.fontDisplay
                        font.pixelSize: 8
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.5
                        color: section._mark
                        opacity: 0.85
                    }
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: 38
                        implicitHeight: 38
                        radius: 4
                        color: section._mark
                        Label {
                            anchors.centerIn: parent
                            text: "彫"
                            font.family: Theme.fontKanji
                            font.pixelSize: 24
                            color: Theme.whiteWash
                        }
                    }
                }

                // ---- Name --------------------------------------------
                Label {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    text: card._name
                    // Body face, regular weight, slightly enlarged -- a
                    // proper-name title carries by size, not by a
                    // faux-bold of the single-weight body face (§3.4).
                    font.pixelSize: Theme.fsBody + 3
                    font.weight: Theme.wRegular
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                }

                // ---- Expand chevron ----------------------------------
                Label {
                    visible: card._hasDesc
                    Layout.alignment: Qt.AlignVCenter
                    text: card._expanded ? "▲" : "▼"
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }

                // ---- Remove handle -- hover-revealed crimson cross ---
                // Holder is fixed-width so the row doesn't shift
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
                        ToolTip.text: qsTr("Remove this tattoo")
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
                    color: section._mark
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
