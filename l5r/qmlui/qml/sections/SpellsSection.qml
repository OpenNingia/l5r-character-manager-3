// Copyright (C) 2014-2026 Daniele Simonetti
// Spells section (呪 -- ju, "spell / incantation") -- replaces the spell
// half of the legacy l5r/ui/tabs/techniques.py. (The tech half is its
// own QML section, `techniques`, per the QML tab taxonomy.)
//
// Design intent: "The Spellbook." A shugenja's spells are prayers to the
// kami of the five elements; they are not bought with experience but
// granted as the priest's understanding deepens, while a rare bushi or
// courtier may memorize a single scroll at a cost. So the page reads as
// a register of the incantations the character can call upon. The header
// names the elemental leanings the character's school grants -- the
// AFFINITY they cast with ease and the DEFICIENCY that resists them --
// since those gate which spells lie within reach. Each spell is a card
// stamped on the left with its MASTERY rank inside an element-coloured
// tile (the §2.3 ring palette is the primary visual hook, exactly as in
// Kata / Kiho), the spell name as the title, an ELEMENT · ORIGIN
// subtitle, and -- on the right -- the XP a memorized spell cost. Click
// a card to expand its casting line (range / area / duration / raises),
// tags and full description inline.
//
// A spell reaches the register through one of three channels, flagged so
// the card can act on each correctly:
//   - SCHOOL    -- granted by a rank advancement; not removable here, but
//                  swappable in place (change one granted spell for another
//                  without unwinding the rank -- a correction / GM override).
//   - LEARNED   -- a free-form spell, learned at no cost; removable.
//   - MEMORIZED -- carries an XP cost equal to its mastery; can be
//                  forgotten (refunding the cost).
// The head of the panel carries a quiet gold "Learn a Spell" affordance
// that opens BuySpellDialog (a QML-native catalogue gating each spell on
// the caster's mastery reach, with element + tag/maho filters).
//
// Data contract expected from the proxy (degrades gracefully to the
// empty-state when missing):
//   pcProxy.spells: [
//     { id, name,
//       element:      "fire",          // ring key, or "multi"/"dragon"
//       elementLabel: "Fire",          // multi -> "Air, Fire"
//       mastery:      3,
//       masteryMod:   1,               // affinity(+) / deficiency(-)
//       range, area, duration,         // casting line
//       raises:       "Range, Area",
//       tags:         ["attack"],
//       source:       "Core p.182",
//       description:  "…",
//       isSchool, isLearned, isMemorized,
//       cost:         0 },             // XP paid (memo cost, else 0)
//     ...
//   ]
//   pcProxy.spellAffinities / pcProxy.spellDeficiencies : ["Fire", …]
//   pcProxy.isShugenja : bool
// Required controller methods on appCtrl:
//   learnSpell(id) · removeSpell(id) · memorizeSpell(id) · forgetSpell(id)
//   replaceSchoolSpell(oldId, newId)   (the school-spell swap)
//   availableSpellsToBuy() -> [...]  (consumed by the dialog, both modes)
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
    // Defensive bindings -- proxy may be absent on first paint or under
    // the offscreen preview tool (which binds a null pcProxy).
    // -----------------------------------------------------------------
    readonly property var _spells: (pcProxy && pcProxy.spells) ? pcProxy.spells : []
    readonly property bool _hasSpells: _spells.length > 0
    readonly property var _affinities: (pcProxy && pcProxy.spellAffinities) ? pcProxy.spellAffinities : []
    readonly property var _deficiencies: (pcProxy && pcProxy.spellDeficiencies) ? pcProxy.spellDeficiencies : []
    readonly property bool _isShugenja: (pcProxy && pcProxy.isShugenja) ? pcProxy.isShugenja : false

    // Pending shugenja choices the school grants -- all resolved here. They
    // surface as §6.16 callouts in priority order (affinity -> deficiency ->
    // free spells): the elemental leanings set which masteries lie within
    // reach, so they are chosen before the spells judged against them.
    readonly property int _affinityChoices: (pcProxy && pcProxy.affinityChoiceCount) ? pcProxy.affinityChoiceCount : 0
    readonly property int _deficiencyChoices: (pcProxy && pcProxy.deficiencyChoiceCount) ? pcProxy.deficiencyChoiceCount : 0
    readonly property bool _freeSpellPending: (pcProxy && pcProxy.freeSpellChoicePending) ? pcProxy.freeSpellChoicePending : false

    // The header strip of elemental leanings is meaningful only when the
    // school grants one or the character is a priest -- a bushi who has
    // merely memorized a scroll has no affinity to report.
    readonly property bool _showLeanings: _isShugenja || _affinities.length > 0 || _deficiencies.length > 0

    // Total XP committed to memorized spells -- the footer coda. Most
    // spells are free; only memorized ones carry a cost.
    readonly property int _spentXp: {
        var n = 0;
        for (var i = 0; i < _spells.length; ++i)
            n += (_spells[i].cost || 0);
        return n;
    }

    // Id of the currently-expanded spell, or "" for none. A single id
    // (not per-card toggles) so opening one collapses the previous,
    // keeping a long spellbook compact while reading -- mirrors Kata.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    // Ring hue for a spell's element, or gold for multi/dragon spells
    // (which fall outside the §2.3 ring palette).
    function _ringColorFor(key) {
        if (key === "earth" || key === "air" || key === "water" || key === "fire" || key === "void")
            return Theme.ringColor(key);
        return Theme.heading;
    }

    function _requestRemove(item) {
        if (item && appCtrl)
            appCtrl.removeSpell(item.id);
    }

    // Change a school-granted spell for another. School spells cannot be
    // removed here (they belong to a rank advancement), but they can be
    // swapped in place -- the fix for a mis-picked spell or a GM-requested
    // change, without unwinding the whole rank. Reuses the learn dialog in
    // its "swap" mode (no mastery-reach gate: a GM override).
    function _requestSwap(item) {
        if (item && item.id)
            buySpellDlg.presentSwap(item.id, item.name || "");
    }

    // The memorize toggle: forget when already memorized (refunding the
    // XP), otherwise memorize (spending it). The api setter owns the
    // dirty flag and surfaces the not-enough-XP notice.
    function _toggleMemorize(item) {
        if (!item || !appCtrl)
            return;
        if (item.isMemorized)
            appCtrl.forgetSpell(item.id);
        else
            appCtrl.memorizeSpell(item.id);
    }

    // -----------------------------------------------------------------
    // Inline spell chooser -- replaces the freeform legacy SpellAdvDialog.
    // -----------------------------------------------------------------
    Dialogs.BuySpellDialog {
        id: buySpellDlg
    }

    // -----------------------------------------------------------------
    // Bounded choosers for the school-granted opportunities: the tabbed
    // spell picker (free spells) and the shared element picker (affinity /
    // deficiency). Replace the legacy bounded SpellAdvDialog and the bare
    // affinity/deficiency QInputDialogs.
    // -----------------------------------------------------------------
    Dialogs.ChooseSchoolSpellsDialog {
        id: chooseSchoolSpellsDlg
    }
    Dialogs.ChooseElementDialog {
        id: chooseElementDlg
    }

    // -----------------------------------------------------------------
    // Opportunity callouts (§6.16). The in-section landing for the Spells
    // TOC badge -- shown one at a time in priority order so the player fixes
    // the elemental leanings before choosing spells against them. Accent-blue
    // per the positive-action language (crimson is reserved for
    // destructive/unmet).
    // -----------------------------------------------------------------
    SpellCallout {
        Layout.fillWidth: true
        visible: section._affinityChoices > 0
        seal: "氣"
        heading: qsTr("YOUR SCHOOL AWAKENS AN AFFINITY")
        subtitle: qsTr("choose the element your prayers command with ease")
        action: qsTr("Choose Affinity")
        onActivated: chooseElementDlg.present("affinity")
    }
    SpellCallout {
        Layout.fillWidth: true
        visible: section._affinityChoices === 0 && section._deficiencyChoices > 0
        seal: "氣"
        heading: qsTr("YOUR SCHOOL EXACTS A DEFICIENCY")
        subtitle: qsTr("choose the element whose kami resist your call")
        action: qsTr("Choose Deficiency")
        onActivated: chooseElementDlg.present("deficiency")
    }
    SpellCallout {
        Layout.fillWidth: true
        visible: section._affinityChoices === 0 && section._deficiencyChoices === 0 && section._freeSpellPending
        seal: "呪"
        heading: qsTr("YOUR SCHOOL GRANTS SPELLS")
        subtitle: qsTr("the kami offer their prayers — choose those within your reach")
        action: qsTr("Choose Spells")
        onActivated: chooseSchoolSpellsDlg.present()
    }

    // -----------------------------------------------------------------
    // The whole spellbook lives on a single parchment SheetPanel. Being
    // a Pane, it forces ink-on-paper palette onto every descendant
    // Label, so the cards stay legible even on a dark OS theme.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Spells")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count + add affordance -------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("the incantations you may call upon the kami to grant")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasSpells
                    text: section._spells.length === 1 ? qsTr("1 spell") : qsTr("%1 spells").arg(section._spells.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }

                // Gold-outlined add affordance -- ink-on-paper button,
                // same vocabulary as Kata's "Learn a Kata".
                Button {
                    id: learnSpellBtn
                    text: qsTr("＋  Learn a Spell")
                    onClicked: buySpellDlg.present()
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 14
                    rightPadding: 14

                    contentItem: Label {
                        text: learnSpellBtn.text
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsBody
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.6
                        color: Theme.heading
                        opacity: learnSpellBtn.hovered ? 1.0 : 0.88
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        // Gold wash derived from the heading token (not a
                        // free hex) -- warms on hover, deepens on press.
                        color: learnSpellBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : learnSpellBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
                        border.width: 1
                        border.color: Theme.heading
                        radius: 1
                    }
                }
            }

            // ---- Elemental leanings: affinity / deficiency -----------
            // The school's elemental gifts and resistances -- the legacy
            // tab showed these above the spell table because they set
            // which masteries are within reach.
            ColumnLayout {
                visible: section._showLeanings
                Layout.fillWidth: true
                Layout.topMargin: 2
                spacing: 4

                LeaningRow {
                    Layout.fillWidth: true
                    caption: qsTr("AFFINITY")
                    accent: Theme.positive
                    values: section._affinities
                }
                LeaningRow {
                    Layout.fillWidth: true
                    caption: qsTr("DEFICIENCY")
                    accent: Theme.accent
                    values: section._deficiencies
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
                visible: !section._hasSpells
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    Label {
                        anchors.centerIn: parent
                        text: "呪"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.heading
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No spells known yet.")
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
                    text: section._isShugenja ? qsTr("As your Insight deepens, the kami grant you their spells. Learn one whose mastery lies within your reach.") : qsTr("Spells are the province of shugenja, though a rare soul may memorize a single scroll. Learn one whose mastery lies within your reach.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The spellbook ---------------------------------------
            // Sorted in the proxy by mastery descending, then element
            // ("magic school"), then name; rendered as a single flat
            // scroll, the element-coloured mastery stamp on each card
            // carrying both rank and element at a glance.
            Repeater {
                model: section._spells
                delegate: SpellCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Footer coda -----------------------------------------
            Widgets.OrnateDivider {
                visible: section._hasSpells
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                visible: section._hasSpells
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: section._spentXp > 0 ? qsTr("%1 spells known · %2 experience spent memorizing").arg(section._spells.length).arg(section._spentXp) : qsTr("%1 spells inscribed in your library").arg(section._spells.length)
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
    // LeaningRow -- one elemental-leaning line ("AFFINITY: Fire, Water").
    // The values render as small outlined chips in the leaning's hue;
    // an empty set reads as a quiet "None".
    // =================================================================
    component LeaningRow: RowLayout {
        id: leaning
        property string caption: ""
        property color accent: Theme.ink
        property var values: []

        spacing: 8

        Label {
            Layout.preferredWidth: 80
            text: leaning.caption
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsCaption
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.6
            color: Theme.heading
            opacity: 0.85
        }
        Flow {
            Layout.fillWidth: true
            spacing: 6

            Label {
                visible: leaning.values.length === 0
                text: qsTr("None")
                font.italic: true
                font.pixelSize: Theme.fsCaption
                color: Theme.ink
                opacity: 0.5
            }
            Repeater {
                model: leaning.values
                delegate: Rectangle {
                    implicitHeight: 18
                    implicitWidth: leanLabel.implicitWidth + 16
                    radius: 9
                    color: "transparent"
                    border.width: 1
                    border.color: leaning.accent
                    opacity: 0.9
                    Label {
                        id: leanLabel
                        anchors.centerIn: parent
                        text: (modelData || "").toUpperCase()
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsMicro
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.2
                        color: leaning.accent
                    }
                }
            }
        }
    }

    // =================================================================
    // SpellCallout -- a §6.16 opportunity banner (36×36 kanji tile + two
    // lines + a CTA). One shape for all three school-granted prompts; the
    // host sets seal / heading / subtitle / action and handles activated().
    // =================================================================
    component SpellCallout: Rectangle {
        id: callout
        property string seal: ""
        property string heading: ""
        property string subtitle: ""
        property string action: ""
        signal activated

        implicitHeight: 56
        color: Theme.secondarySoft
        border.color: Theme.secondary
        border.width: 1
        radius: 2

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 12

            // 36×36 kanji tile (§6.16: smaller than the dialog's 48px).
            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                Layout.alignment: Qt.AlignVCenter
                radius: 4
                color: Theme.secondary
                Label {
                    anchors.centerIn: parent
                    text: callout.seal
                    font.family: Theme.fontKanji
                    font.pixelSize: 24
                    color: Theme.whiteWash
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Label {
                    text: callout.heading
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading2
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.4
                    color: Theme.secondary
                }
                Label {
                    Layout.fillWidth: true
                    text: callout.subtitle
                    font.family: Theme.fontBody
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                    wrapMode: Text.WordWrap
                }
            }
            Widgets.L5RButton {
                text: callout.action
                glyph: callout.seal
                accent: Theme.secondary
                accentDark: Theme.secondaryDark
                Layout.alignment: Qt.AlignVCenter
                onClicked: callout.activated()
            }
        }
    }

    // =================================================================
    // SpellCard -- one known spell. Defined inline (no reuse outside
    // this section). The card carries an element-coloured mastery stamp
    // on the left, the name + ELEMENT · ORIGIN subtitle in the middle,
    // the memorized-XP rail on the right, hover-revealed memorize /
    // remove handles, and an inline casting line + description on tap.
    // =================================================================
    component SpellCard: Rectangle {
        id: card
        property var item: null

        readonly property string _name: (item && item.name) ? item.name : qsTr("(unnamed spell)")
        readonly property string _elementKey: (item && item.element) ? item.element : "void"
        readonly property string _elementLabel: (item && item.elementLabel) ? item.elementLabel : ""
        readonly property color _ringColor: section._ringColorFor(_elementKey)
        readonly property int _mastery: (item && item.mastery) ? item.mastery : 0
        readonly property int _masteryMod: (item && item.masteryMod) ? item.masteryMod : 0
        readonly property int _cost: (item && item.cost !== undefined) ? item.cost : 0
        readonly property string _desc: (item && item.description) ? item.description : ""
        readonly property string _range: (item && item.range) ? item.range : ""
        readonly property string _area: (item && item.area) ? item.area : ""
        readonly property string _duration: (item && item.duration) ? item.duration : ""
        readonly property string _raises: (item && item.raises) ? item.raises : ""
        readonly property var _tags: (item && item.tags) ? item.tags : []
        readonly property bool _isSchool: !!(item && item.isSchool)
        readonly property bool _isLearned: !!(item && item.isLearned)
        readonly property bool _isMemorized: !!(item && item.isMemorized)

        // Origin label: a granted school spell, or one learned free-form.
        // (Memorized state is shown separately, since a spell can be both.)
        readonly property string _origin: _isSchool ? qsTr("SCHOOL") : (_isLearned ? qsTr("LEARNED") : "")
        // Only free-form spells can be removed here, and only while not
        // memorized -- forget the memorized copy first (mirrors legacy).
        readonly property bool _removable: _isLearned && !_isMemorized
        readonly property bool _hasDetail: _desc.length > 0 || _range.length > 0 || _area.length > 0 || _duration.length > 0 || _raises.length > 0
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

        // Left rail accent -- the element-hued strip that ties the spell
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
            cursorShape: card._hasDetail ? Qt.PointingHandCursor : Qt.ArrowCursor
        }
        // Whole-card tap toggles the detail (only meaningful when there
        // is something to show).
        TapHandler {
            enabled: card._hasDetail
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

                // ---- Name + element · origin subtitle ----------------
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
                    // ELEMENT · ORIGIN + the affinity/deficiency mark +
                    // a MEMORIZED pill. The element label is the primary
                    // ring-hued hook (matching Kata/Kiho); origin follows
                    // in a quieter ink.
                    Flow {
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
                            visible: card._elementLabel.length > 0 && card._origin.length > 0
                            text: "·"
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.4
                        }
                        Label {
                            visible: card._origin.length > 0
                            text: card._origin
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.letterSpacing: 1.4
                            font.weight: Theme.wSemiBold
                            // School spells are gifts (gold); free-form
                            // ones a quieter ink.
                            color: card._isSchool ? Theme.heading : Theme.ink
                            opacity: card._isSchool ? 0.85 : 0.55
                        }
                        // Affinity / deficiency mark -- the casting ease
                        // (+) or resistance (-) toward this element.
                        Label {
                            visible: card._masteryMod !== 0
                            text: card._masteryMod > 0 ? qsTr("AFFINITY +%1").arg(card._masteryMod) : qsTr("DEFICIENCY %1").arg(card._masteryMod)
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.fsCaption
                            font.letterSpacing: 1.2
                            font.weight: Theme.wSemiBold
                            color: card._masteryMod > 0 ? Theme.positive : Theme.accent
                            opacity: 0.9
                        }
                        // MEMORIZED pill -- the spell carries an XP cost
                        // and may be forgotten.
                        Rectangle {
                            visible: card._isMemorized
                            height: 16
                            width: memoPill.implicitWidth + 14
                            radius: 8
                            color: "transparent"
                            border.width: 1
                            border.color: Theme.inkMuted
                            Label {
                                id: memoPill
                                anchors.centerIn: parent
                                text: qsTr("MEMORIZED")
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.0
                                color: Theme.inkMuted
                            }
                        }
                    }
                }

                // ---- XP-paid rail (memorized spells only) ------------
                ColumnLayout {
                    visible: card._isMemorized && card._cost > 0
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: 40
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
                    visible: card._hasDetail
                    Layout.alignment: Qt.AlignVCenter
                    text: card._expanded ? "▲" : "▼"
                    font.pixelSize: 9
                    color: Theme.ink
                    opacity: 0.45
                }

                // ---- Memorize / forget handle -- hover-revealed ------
                // A small scroll toggle: outline when the spell may be
                // memorized, filled gold once it is. Holder is fixed-
                // width so the row doesn't dance as it fades in.
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter

                    AbstractButton {
                        id: memoBtn
                        anchors.fill: parent
                        visible: cardHover.hovered || memoBtn.hovered || card._isMemorized
                        onClicked: section._toggleMemorize(card.item)

                        background: Rectangle {
                            radius: 11
                            color: card._isMemorized ? Theme.heading : (memoBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.14) : "transparent")
                            border.color: Theme.heading
                            border.width: 1
                            opacity: (card._isMemorized || memoBtn.hovered) ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "巻"   // scroll -- the memorized codex
                            font.family: Theme.fontKanji
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: card._isMemorized ? Theme.whiteWash : Theme.heading
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: card._isMemorized ? qsTr("Forget this memorized spell (refunds %1 XP)").arg(card._mastery) : qsTr("Memorize this spell (%1 XP)").arg(card._mastery)
                    }
                }

                // ---- Swap handle -- hover-revealed, school spells only --
                // School spells belong to a rank advancement and cannot be
                // removed here, but they can be swapped in place: a "換"
                // (change) affordance in the blue action hue, distinct from
                // the gold memorize toggle and the crimson remove cross.
                // A correction / GM-override, so it has no reach gate.
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter
                    visible: card._isSchool

                    AbstractButton {
                        id: swapBtn
                        anchors.fill: parent
                        visible: cardHover.hovered || swapBtn.hovered
                        onClicked: section._requestSwap(card.item)

                        background: Rectangle {
                            radius: 11
                            color: swapBtn.hovered ? Theme.secondary : "transparent"
                            border.color: Theme.secondary
                            border.width: 1
                            opacity: swapBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "換"   // exchange -- swap this school spell
                            font.family: Theme.fontKanji
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: swapBtn.hovered ? Theme.whiteWash : Theme.secondary
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: qsTr("Change this school spell")
                    }
                }

                // ---- Remove handle -- hover-revealed crimson cross ---
                // Only for free-form learned spells; school spells live
                // on a rank advancement and have no handle here.
                Item {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    Layout.alignment: Qt.AlignVCenter
                    visible: card._removable

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
                        ToolTip.text: qsTr("Forget this spell")
                    }
                }
            }

            // ---- Expanded detail -- casting line, tags, description --
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 50
                visible: card._expanded && card._hasDetail
                spacing: 6

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: card._ringColor
                    opacity: 0.25
                }

                // Casting line -- only the fields the datapack fills in.
                Flow {
                    Layout.fillWidth: true
                    visible: card._range.length > 0 || card._area.length > 0 || card._duration.length > 0 || card._raises.length > 0
                    spacing: 18

                    Repeater {
                        model: [
                            { k: qsTr("RANGE"), v: card._range },
                            { k: qsTr("AREA"), v: card._area },
                            { k: qsTr("DURATION"), v: card._duration },
                            { k: qsTr("RAISES"), v: card._raises }
                        ]
                        delegate: ColumnLayout {
                            visible: (modelData.v || "").length > 0
                            spacing: 0
                            Label {
                                text: modelData.k
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.6
                                color: Theme.heading
                                opacity: 0.8
                            }
                            Label {
                                text: modelData.v
                                font.pixelSize: Theme.fsCaption
                                color: Theme.ink
                                opacity: 0.85
                            }
                        }
                    }
                }

                // Tags -- quiet outlined chips.
                Flow {
                    Layout.fillWidth: true
                    visible: card._tags.length > 0
                    spacing: 6

                    Repeater {
                        model: card._tags
                        delegate: Rectangle {
                            implicitHeight: 18
                            implicitWidth: cardTagLabel.implicitWidth + 14
                            radius: 9
                            color: "transparent"
                            border.width: 1
                            border.color: Theme.borderSubtle
                            Label {
                                id: cardTagLabel
                                anchors.centerIn: parent
                                text: (modelData || "").toUpperCase()
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.0
                                color: Theme.inkMuted
                            }
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    Layout.bottomMargin: 2
                    visible: card._desc.length > 0
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
