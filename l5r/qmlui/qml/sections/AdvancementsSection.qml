// Copyright (C) 2014-2026 Daniele Simonetti
// Advancements section -- the character's training ledger. Replaces
// l5r/ui/tabs/advancements.py.
// Design intent: a kakemono-scroll chronicle. The page reads top-down
// like an unfurled scroll -- a stamped ledger banner at the top with
// total XP spent / entries / current rank, then a vertical timeline of
// inked entries with brush-kanji seals down the rail. The most recent
// entry (the head of the stack) is the only one that can be refunded;
// older entries are read-only history, which matches the stack-pop
// semantics of l5r.api.advancements.refund_last_advancement.
// Data contract expected from the proxy (degrades gracefully when
// missing -- the section renders the empty-state):
//   pcProxy.advancements: [
//     { type: "skill"|"attrib"|"void"|"perk"|"kata"|"kiho"
//             |"spell"|"memo_spell"|"emph",
//       desc:      "Kenjutsu rank 1 -> 2",
//       cost:      4,
//       timestamp: 1716800000,   // unix seconds
//       isHead:    true          // true only for items[0] (most recent)
//     }, ...
//   ]
//   pcProxy.advancementsXpSpent: number       // sum of costs
//   pcProxy.advancementsCount:   number       // length of the list
//   appCtrl.refundLastAdvancement(): void
//   appCtrl.resetAdvancements():     void      // clears the whole stack
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // -----------------------------------------------------------------
    // Defensive bindings -- the QML side runs before the proxy is
    // bound on first paint, and proxy properties may be absent on
    // older builds. Read-once via the safe accessors below.
    // -----------------------------------------------------------------
    readonly property var _items: (pcProxy && pcProxy.advancements) ? pcProxy.advancements : []
    readonly property int _count: (pcProxy && pcProxy.advancementsCount !== undefined) ? pcProxy.advancementsCount : section._items.length
    readonly property int _xpSpent: (pcProxy && pcProxy.advancementsXpSpent !== undefined) ? pcProxy.advancementsXpSpent : 0
    readonly property int _rank: (pcProxy && pcProxy.progression) ? pcProxy.progression.rank : 0
    readonly property bool _hasItems: section._items.length > 0

    // -----------------------------------------------------------------
    // Local filter state. Filters apply to the rendered list only --
    // refund still pops the actual stack head regardless of filter so
    // the semantics never silently change with a chip selection.
    // -----------------------------------------------------------------
    property string _filter: "all"
    readonly property var _filterDefs: [{
            "key": "all",
            "label": qsTr("All")
        }, {
            "key": "skill",
            "label": qsTr("Skills")
        }, {
            "key": "attrib",
            "label": qsTr("Traits")
        }, {
            "key": "perk",
            "label": qsTr("Advantages")
        }, {
            "key": "spell",
            "label": qsTr("Spells")
        }, {
            "key": "kata",
            "label": qsTr("Disciplines")
        }]

    // -----------------------------------------------------------------
    // Type metadata -- kanji glyph, accent colour, and human label per
    // advancement type. The kanji is rendered in Theme.fontKanji (the
    // bundled Kouzan brush face); Cinzel has no CJK coverage and would
    // fall back to the OS font otherwise.
    // -----------------------------------------------------------------
    function _meta(t) {
        switch (t) {
        case "attrib":
            return {
                "kanji": "力",
                "color": Theme.ringEarth,
                "label": qsTr("Trait")
            };
        case "void":
            return {
                "kanji": "空",
                "color": Theme.ringVoid,
                "label": qsTr("Void")
            };
        case "skill":
            return {
                "kanji": "技",
                "color": Theme.secondary,
                "label": qsTr("Skill")
            };
        case "emph":
            return {
                "kanji": "妙",
                "color": Theme.secondary,
                "label": qsTr("Emphasis")
            };
        case "perk":
            return {
                "kanji": "縁",
                "color": Theme.highlight,
                "label": qsTr("Advantage")
            };
        case "kata":
            return {
                "kanji": "型",
                "color": Theme.accent,
                "label": qsTr("Kata")
            };
        case "kiho":
            return {
                "kanji": "拳",
                "color": Theme.accent,
                "label": qsTr("Kiho")
            };
        case "spell":
            return {
                "kanji": "呪",
                "color": Theme.ringFire,
                "label": qsTr("Spell")
            };
        case "memo_spell":
            return {
                "kanji": "記",
                "color": Theme.ringFire,
                "label": qsTr("Memorised")
            };
        default:
            return {
                "kanji": "印",
                "color": Theme.heading,
                "label": t || qsTr("Entry")
            };
        }
    }

    function _fmtTimestamp(ts) {
        if (!ts)
            return "";
        var d = new Date(ts * 1000);
        var pad = function (n) {
            return n < 10 ? "0" + n : "" + n;
        };
        return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + "  " + pad(d.getHours()) + ":" + pad(d.getMinutes());
    }

    function _passesFilter(item) {
        if (section._filter === "all")
            return true;
        if (section._filter === "skill")
            return item.type === "skill" || item.type === "emph";
        if (section._filter === "spell")
            return item.type === "spell" || item.type === "memo_spell";
        if (section._filter === "kata")
            return item.type === "kata" || item.type === "kiho";
        return item.type === section._filter;
    }

    function _filteredItems() {
        if (section._filter === "all")
            return section._items;
        var out = [];
        for (var i = 0; i < section._items.length; ++i) {
            if (section._passesFilter(section._items[i]))
                out.push(section._items[i]);
        }
        return out;
    }

    // -----------------------------------------------------------------
    // Ledger banner -- three hero numbers stacked under a kanji
    // watermark. Reads like the colophon on the first leaf of a scroll.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Ledger of Training")

        RowLayout {
            width: parent.width
            spacing: 0

            // Hero metric: XP invested
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1   // equal split; see banner note
                Layout.alignment: Qt.AlignTop
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("EXPERIENCE SPENT")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._xpSpent
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatLarge
                    font.weight: Theme.wSemiBold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.accent
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("points logged across the chronicle")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.6
                    wrapMode: Text.WordWrap
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                color: Theme.heading
                opacity: 0.25
            }

            // Hero metric: entries logged
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1   // equal split; see banner note
                Layout.alignment: Qt.AlignTop
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("ENTRIES")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._count
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatLarge
                    font.weight: Theme.wSemiBold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("inked since the brush was first lifted")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.6
                    wrapMode: Text.WordWrap
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                color: Theme.heading
                opacity: 0.25
            }

            // Hero metric: current rank (mirrors Character section so
            // the player can see at-a-glance which insight tier this
            // history feeds into).
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 1   // equal split; see banner note
                Layout.alignment: Qt.AlignTop
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("CURRENT RANK")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._rank
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatLarge
                    font.weight: Theme.wSemiBold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("insight tier reached")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.6
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Chronicle -- the timeline itself. SheetPanel sub-header has a
    // filter chip row on the right; the body is a column of dated
    // cards. Each card has a brush-kanji seal on the left rail; the
    // head-of-stack card is foregrounded with a thicker crimson rail,
    // a "LATEST" stamp, and the inline Refund control.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Chronicle")

        ColumnLayout {
            width: parent.width
            spacing: 10

            // ---- Filter chips ----------------------------------------
            // The filter row reads as a margin note -- a quiet caption
            // ("filter:") followed by a horizontal chip strip. Chips use
            // a flat ghost style by default and fill with the accent
            // when active; this keeps the visual weight on the entries
            // themselves rather than the filter UI.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8
                visible: section._hasItems

                Label {
                    text: qsTr("filter")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    opacity: 0.6
                }

                Repeater {
                    model: section._filterDefs
                    delegate: AbstractButton {
                        id: chip
                        readonly property bool active: section._filter === modelData.key
                        implicitHeight: 22
                        leftPadding: 10
                        rightPadding: 10
                        onClicked: section._filter = modelData.key

                        background: Rectangle {
                            radius: 11
                            color: chip.active ? Theme.accent : "transparent"
                            border.color: chip.active ? Theme.accent : Theme.borderSubtle
                            border.width: 1
                        }
                        contentItem: Label {
                            text: modelData.label
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.weight: Font.DemiBold
                            font.letterSpacing: 1.2
                            color: chip.active ? Theme.parchmentBase : Theme.ink
                            opacity: chip.active ? 1.0 : 0.85
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        HoverHandler {
                            id: chipHover
                        }
                        opacity: chip.active || chipHover.hovered ? 1.0 : 0.75
                        Behavior on opacity  {
                            NumberAnimation {
                                duration: 120
                            }
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                Label {
                    visible: section._filter !== "all"
                    text: qsTr("showing %1 of %2").arg(section._filteredItems().length).arg(section._items.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    opacity: 0.55
                }
            }

            // ---- Empty state ----------------------------------------
            // A first-roll character has no advancements. Rather than
            // collapse the panel, paint a generous empty plaque with a
            // kanji watermark and a quiet line of guidance. The kanji
            // here is shuu (cultivate / study / training) -- it matches
            // the section's TOC icon and reads as "no training yet".
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                Layout.topMargin: 12
                visible: !section._hasItems
                spacing: 6

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 110
                    Label {
                        anchors.centerIn: parent
                        text: "修"   // 修
                        font.family: Theme.fontKanji
                        font.pixelSize: 140
                        color: Theme.accent
                        opacity: 0.18
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("The brush awaits.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.5
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 480
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("No advancements have yet been recorded for this samurai. " + "Purchase a trait, skill, or technique on its own tab and the " + "entry will appear here, atop the stack.")
                    font.italic: true
                    font.pixelSize:Theme.fsBody 
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- Timeline list --------------------------------------
            // ListView (not Repeater) so a long history virtualises.
            // Height is bound to contentHeight so SheetPanel's layout
            // grows naturally with the entries.
            ListView {
                id: chronicleView
                visible: section._hasItems
                Layout.fillWidth: true
                Layout.preferredHeight: contentHeight
                interactive: false   // outer page is the scroller
                spacing: 8
                model: section._filteredItems()

                delegate: Item {
                    width: chronicleView.width
                    implicitHeight: entryCard.implicitHeight + 4

                    readonly property var _item: modelData
                    readonly property var _meta: section._meta(_item.type)
                    readonly property bool _isHead: !!_item.isHead

                    // Vertical timeline rail running through the card.
                    // A narrow strip at x=14 with a circular node
                    // centred on the seal. Head-of-stack pulls the rail
                    // colour to crimson; older entries keep a quiet
                    // burnt-gold so the eye walks down the stack and
                    // lands on the most recent entry.
                    Rectangle {
                        x: 14
                        y: 0
                        width: 2
                        height: parent.height
                        color: _isHead ? Theme.accent : Theme.heading
                        opacity: _isHead ? 0.85 : 0.35
                        // Top of the very first item rounds; bottom of
                        // the last one trails off via the parent's
                        // listView spacing. Index check is via the
                        // delegate's `index` context property.
                        visible: true
                    }

                    Rectangle {
                        id: railNode
                        x: 9
                        y: 22
                        width: 12
                        height: 12
                        radius: 6
                        color: _meta.color
                        border.color: Theme.parchment
                        border.width: 2
                        // Faint outer aura on the head node so the eye
                        // catches it at a glance.
                        Rectangle {
                            visible: _isHead
                            anchors.centerIn: parent
                            width: 22
                            height: 22
                            radius: 11
                            color: "transparent"
                            border.color: Theme.accent
                            border.width: 1
                            opacity: 0.55
                        }
                    }

                    // The entry card itself, sat to the right of the
                    // timeline rail.
                    Rectangle {
                        id: entryCard
                        x: 34
                        width: parent.width - 34
                        // Auto-size to inner column.
                        implicitHeight: cardBody.implicitHeight + 22

                        color: _isHead ? Theme.parchmentBase : Theme.parchmentInset
                        border.color: _isHead ? Theme.accentMuted : Theme.borderSubtle
                        border.width: _isHead ? 1 : 1
                        opacity: _isHead ? 1.0 : 0.92
                        radius: 2

                        // Crimson left edge accent on the head card --
                        // turns the rectangle into a "sealed scroll
                        // segment" rather than just a row in a table.
                        Rectangle {
                            visible: _isHead
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            width: 3
                            color: Theme.accent
                        }

                        // Faint "LATEST" / 最新 stamp -- top right of
                        // the head card. The stamp is rotated a few
                        // degrees so it reads as a brush mark rather
                        // than a UI badge.
                        Item {
                            visible: _isHead
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.topMargin: 6
                            anchors.rightMargin: 10
                            width: stampLabel.width + 8
                            height: stampLabel.height + 4
                            Rectangle {
                                anchors.fill: parent
                                color: "transparent"
                                border.color: Theme.accent
                                border.width: 1
                                opacity: 0.75
                                radius: 1
                            }
                            Label {
                                id: stampLabel
                                anchors.centerIn: parent
                                text: qsTr("LATEST")
                                font.family: Theme.fontDisplay
                                font.pixelSize: 9
                                font.weight: Theme.headingWeight
                                font.letterSpacing: 2.0
                                color: Theme.accent
                            }
                            rotation: -4
                            opacity: 0.85
                        }

                        RowLayout {
                            id: cardBody
                            anchors.fill: parent
                            anchors.margins: 12
                            anchors.leftMargin: _isHead ? 16 : 12
                            spacing: 14

                            // Seal column -- brush kanji + tiny type
                            // label below it. Coloured per type so the
                            // eye can scan a long chronicle by hue.
                            ColumnLayout {
                                Layout.preferredWidth: 56
                                Layout.alignment: Qt.AlignTop
                                spacing: 0
                                Label {
                                    Layout.fillWidth: true
                                    text: _meta.kanji
                                    font.family: Theme.fontKanji
                                    font.pixelSize: 40
                                    horizontalAlignment: Text.AlignHCenter
                                    color: _meta.color
                                    opacity: 0.92
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: _meta.label.toUpperCase()
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: 9
                                    font.weight: Theme.headingWeight
                                    font.letterSpacing: 1.6
                                    horizontalAlignment: Text.AlignHCenter
                                    color: _meta.color
                                    opacity: 0.85
                                }
                            }

                            // Body column -- description (main line) +
                            // timestamp underneath. The description
                            // uses the OS body font so long entries
                            // ("Skill 'Lore: Shugenja' rank 2 -> 3")
                            // wrap legibly; Cinzel here would crowd.
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 4
                                Label {
                                    Layout.fillWidth: true
                                    text: _item.desc || qsTr("(unnamed advancement)")
                                    font.pixelSize:Theme.fsBody  + 1
                                    font.weight: Font.DemiBold
                                    color: Theme.ink
                                    wrapMode: Text.WordWrap
                                    elide: Text.ElideRight
                                    maximumLineCount: 2
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        text: section._fmtTimestamp(_item.timestamp)
                                        font.italic: true
                                        font.pixelSize: Theme.fsCaption
                                        font.features: Theme.tabularNumbers
                                        opacity: 0.6
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 3
                                        Layout.preferredHeight: 3
                                        radius: 1.5
                                        color: Theme.ink
                                        opacity: 0.35
                                    }
                                    Label {
                                        text: _meta.label
                                        font.pixelSize: Theme.fsCaption
                                        opacity: 0.6
                                    }
                                    Item {
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            // Cost column -- right-aligned hero number
                            // in Cinzel, then a "XP" caption beneath.
                            // The head card swaps in a refund control
                            // below the cost so the destructive action
                            // is anchored to the card it acts on.
                            ColumnLayout {
                                Layout.preferredWidth: 90
                                Layout.alignment: Qt.AlignTop
                                spacing: 2

                                Label {
                                    Layout.fillWidth: true
                                    text: _item.cost
                                    font.family: Theme.fontStat
                                    font.pixelSize: Theme.fsStatMedium
                                    font.weight: Theme.wMedium
                                    font.features: Theme.tabularNumbers
                                    horizontalAlignment: Text.AlignRight
                                    color: _isHead ? Theme.accent : Theme.heading
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("XP")
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: 9
                                    font.weight: Theme.headingWeight
                                    font.letterSpacing: 2.0
                                    horizontalAlignment: Text.AlignRight
                                    color: _isHead ? Theme.accent : Theme.heading
                                    opacity: 0.85
                                }

                                Item {
                                    visible: _isHead
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 4
                                }

                                Button {
                                    visible: _isHead
                                    Layout.fillWidth: true
                                    Layout.topMargin: 6
                                    text: qsTr("↩  Refund")
                                    ToolTip.visible: hovered
                                    ToolTip.text: qsTr("Refund this advancement")
                                    onClicked: {
                                        if (!appCtrl)
                                            return;
                                        // Honor the "Do not prompt again" preference -- if the
                                        // user already opted out of the warning, refund inline.
                                        if (appCtrl.refundWarningEnabled && appCtrl.refundWarningEnabled()) {
                                            refundDlg.open();
                                        } else {
                                            appCtrl.refundLastAdvancement();
                                        }
                                    }
                                    background: Rectangle {
                                        radius: 2
                                        color: parent.down ? Theme.accentMuted : (parent.hovered ? Theme.accent : "transparent")
                                        border.color: Theme.accent
                                        border.width: 1
                                    }
                                    contentItem: Label {
                                        text: parent.text
                                        font.family: Theme.fontDisplay
                                        font.pixelSize: Theme.fsCaption
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 1.4
                                        color: parent.hovered ? Theme.parchmentBase : Theme.accent
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ---- Footer: margin note + reset-all --------------------
            // The caption answers the only question the section UX
            // raises ("where's the refund button on the older cards?").
            // The reset-all control sits opposite it: a quiet ghost
            // button until hovered, crimson per §6.16 (destructive),
            // gated behind resetDlg so a slip can't wipe the chronicle.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                visible: section._hasItems
                spacing: 12

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr("Only the most recent advancement may be refunded.")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    opacity: 0.55
                    wrapMode: Text.WordWrap
                }

                Button {
                    id: resetButton
                    text: qsTr("Reset all")
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Clear the entire advancement history")
                    onClicked: resetDlg.open()
                    background: Rectangle {
                        radius: 2
                        color: resetButton.down ? Theme.accentMuted : (resetButton.hovered ? Theme.accent : "transparent")
                        border.color: Theme.accent
                        border.width: 1
                    }
                    contentItem: Label {
                        text: resetButton.text
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1.4
                        color: resetButton.hovered ? Theme.parchmentBase : Theme.accent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Refund confirmation -- inline QML Dialog (no QMessageBox; see
    // feedback_qmlui_no_widget_reuse). Mirrors the legacy warn flow
    // including the "Do not prompt again" affordance; the persistence
    // of that preference is the appCtrl's responsibility (it has access
    // to L5RCMSettings.app.warn_about_refund).
    // -----------------------------------------------------------------
    Dialog {
        id: refundDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        modal: true
        title: qsTr("Refund this advancement?")
        standardButtons: Dialog.NoButton

        readonly property var _head: section._items.length > 0 ? section._items[0] : null

        contentItem: ColumnLayout {
            spacing: 12

            Label {
                Layout.fillWidth: true
                Layout.maximumWidth: 380
                text: qsTr("Refund this advancement and return its XP to your pool?")
                wrapMode: Text.WordWrap
                font.pixelSize:Theme.fsBody 
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.heading
                opacity: 0.35
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                visible: refundDlg._head !== null
                Label {
                    text: refundDlg._head ? section._meta(refundDlg._head.type).kanji : ""
                    font.family: Theme.fontKanji
                    font.pixelSize: 28
                    color: refundDlg._head ? section._meta(refundDlg._head.type).color : Theme.heading
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: refundDlg._head ? refundDlg._head.desc : ""
                        font.weight: Font.DemiBold
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: refundDlg._head ? section._fmtTimestamp(refundDlg._head.timestamp) : ""
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.6
                    }
                }
                Label {
                    text: refundDlg._head ? ("+" + refundDlg._head.cost + " XP") : ""
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatMedium
                    font.weight: Theme.wMedium
                    color: Theme.accent
                }
            }

            CheckBox {
                id: dontAskCheck
                Layout.fillWidth: true
                text: qsTr("Do not prompt again")
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 8

                Item {
                    Layout.fillWidth: true
                }

                Button {
                    text: qsTr("Cancel")
                    onClicked: refundDlg.reject()
                }
                Button {
                    text: qsTr("Refund")
                    background: Rectangle {
                        radius: 2
                        color: parent.down ? Theme.accentMuted : (parent.hovered ? Theme.accent : Theme.accent)
                        border.color: Theme.accentMuted
                        border.width: 1
                    }
                    contentItem: Label {
                        text: parent.text
                        font.family: Theme.fontDisplay
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1.4
                        color: Theme.parchmentBase
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (appCtrl) {
                            if (dontAskCheck.checked && appCtrl.suppressRefundWarning) {
                                appCtrl.suppressRefundWarning();
                            }
                            if (appCtrl.refundLastAdvancement) {
                                appCtrl.refundLastAdvancement();
                            }
                        }
                        refundDlg.accept();
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Reset-all confirmation -- design-system dialog shell (L5RDialog).
    // Distinct from the refund flow: this wipes the WHOLE chronicle, so
    // it always confirms (no "do not prompt again") and reads in crimson
    // (§6.16, destructive). Family and school survive the reset (they are
    // set at creation, not as advancements). 捨 (sutu) -- discard / let go.
    // -----------------------------------------------------------------
    Widgets.L5RDialog {
        id: resetDlg
        title: qsTr("Reset all advancements?")
        tagline: qsTr("Wipe the training ledger")
        seal: "捨"
        accent: Theme.accent
        accentDark: Theme.accentMuted
        padding: Theme.s6
        acceptText: qsTr("Reset everything")
        acceptGlyph: "捨"
        cancelText: qsTr("Keep history")
        onAccepted: if (appCtrl)
            appCtrl.resetAdvancements()

        Label {
            width: 380
            text: qsTr("This clears every advancement in the chronicle and "
                + "refunds all spent experience, returning the character to "
                + "its freshly-created state. Family and school are kept. "
                + "This cannot be undone.")
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }
    }
}
