// Copyright (C) 2014-2026 Daniele Simonetti
// Advantages & Disadvantages section -- replaces l5r/ui/tabs/perks.py.
// Design intent: a balance-scroll, "The Ledger of Fortune & Misfortune"
// (福禍の帳). The page opens with a Tenbin (天秤) banner that puts the
// two ledgers in dialogue -- XP spent on blessings on the left pan, XP
// granted by burdens on the right, with the net effect inked between
// them in the colour of the side that's heavier. Below the banner the
// two registers stack vertically: Blessings (福) over Burdens (禍),
// each as its own SheetPanel with brush-kanji seals, an inline add
// affordance, and per-entry hover-revealed removal. Empty states paint
// a generous watermark plaque rather than collapsing the panel.
// Adding an entry opens InscribePerkDialog (a QML-native two-pane
// catalogue). The dialog suggests the rulebook cost; the player can
// flip an override switch and inscribe a manually-set value -- the
// switch is intentionally muted so the suggested cost is the default
// path and overrides feel like a deliberate house-rule.
// Data contract expected from the proxy (degrades gracefully when
// missing -- the section renders the empty-state):
//   pcProxy.merits: [
//     { advId:   "<uuid or stable handle>",
//       ruleId:  "allies",
//       name:    "Allies",
//       subtype: "Yasuki Trading",          // optional, may be ""
//       rank:    2,                          // 0 if rankless
//       cost:    4,                          // XP paid (may be 0 for starting)
//       isCustom: false,                     // true if cost was overridden
//       isStarting: false                    // true if granted by school
//     }, ...
//   ]
//   pcProxy.flaws: [   // same shape, `cost` is the XP granted (positive number)
//     { advId, ruleId, name, subtype, rank, cost, isCustom, isStarting }, ...
//   ]
//   pcProxy.meritsXp: number      // sum of merit costs
//   pcProxy.flawsXp:  number      // sum of flaw gains
//   pcProxy.perksNetXp: number    // meritsXp - flawsXp (positive = net spend)
//   pcProxy.flawsCap:  number     // 4e house cap (typically 10); 0 = no cap
//   appCtrl.openInscribeMerit(): void     // opens the picker, "merit" mode
//   appCtrl.openInscribeFlaw():  void
//   appCtrl.removePerk(advId):   void     // works for both merits and flaws
// (If the controller hands the picker its catalogue inline, you can
// also drive InscribePerkDialog directly -- see the bottom of this
// file for the embedded instance and its `present(kind)` entrypoint.)
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import "../dialogs" as Dialogs
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.sectionSpacing

    // -----------------------------------------------------------------
    // Defensive bindings -- proxy properties may be absent on first
    // paint or on older builds. Read once, fall back to safe defaults.
    // -----------------------------------------------------------------
    readonly property var _merits: (pcProxy && pcProxy.merits) ? pcProxy.merits : []
    readonly property var _flaws: (pcProxy && pcProxy.flaws) ? pcProxy.flaws : []
    readonly property int _meritsXp: (pcProxy && pcProxy.meritsXp !== undefined) ? pcProxy.meritsXp : section._sumCost(section._merits)
    readonly property int _flawsXp: (pcProxy && pcProxy.flawsXp !== undefined) ? pcProxy.flawsXp : section._sumCost(section._flaws)
    readonly property int _netXp: (pcProxy && pcProxy.perksNetXp !== undefined) ? pcProxy.perksNetXp : (section._meritsXp - section._flawsXp)
    readonly property int _flawsCap: (pcProxy && pcProxy.flawsCap !== undefined) ? pcProxy.flawsCap : 10

    readonly property bool _hasMerits: section._merits.length > 0
    readonly property bool _hasFlaws: section._flaws.length > 0

    function _sumCost(arr) {
        var s = 0;
        for (var i = 0; i < arr.length; ++i)
            s += (arr[i].cost || 0);
        return s;
    }

    // -----------------------------------------------------------------
    // Tenbin banner -- the scale. Three hero numbers ride across a
    // half-transparent brush kanji "天" watermark that anchors the
    // section visually. The middle number (net) is the only one that
    // changes colour: crimson when the soul has net-spent XP on
    // advantages, jade-green when burdens have given more than blessings
    // have taken. This is the only number the player actually plans
    // around at character creation, so it earns the colour swap.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("The Ledger of Fortune & Misfortune")

        Item {
            width: parent.width
            implicitHeight: balanceRow.implicitHeight + 24

            // Brush kanji watermark behind the row.
            Label {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: -8
                anchors.rightMargin: 4
                text: "天"      // ten -- "heaven", the upper hook of 天秤
                font.family: Theme.fontKanji
                font.pixelSize: 150
                color: Theme.heading
                opacity: Theme.watermarkOpacity
            }

            RowLayout {
                id: balanceRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0

                // Left pan -- XP paid for blessings.
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1   // equal split; see banner note
                    Layout.alignment: Qt.AlignTop
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("INVESTED IN BLESSINGS")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.smallFont
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 2.0
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.heading
                        opacity: 0.85
                    }
                    Label {
                        Layout.fillWidth: true
                        text: section._meritsXp
                        font.family: Theme.fontDisplay
                        font.pixelSize: 34
                        font.weight: Font.Bold
                        font.features: Theme.tabularNumbers
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.heading
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("points laid down for advantage")
                        font.italic: true
                        font.pixelSize: Theme.smallFont
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.6
                        wrapMode: Text.WordWrap
                    }
                }

                // The beam of the scale -- a faint hairline + a brushy
                // dot in the middle. Drawn with two thin rectangles so
                // the dot reads as the pivot rather than a bullet.
                Item {
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    Layout.topMargin: 8
                    Layout.bottomMargin: 8
                    Rectangle {
                        anchors.fill: parent
                        color: Theme.heading
                        opacity: 0.25
                    }
                }

                // Center -- the verdict. Crimson if you've net-spent
                // XP, jade if the burdens granted more than the
                // blessings cost (rare but possible at character gen).
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1   // equal split; see banner note
                    Layout.alignment: Qt.AlignTop
                    spacing: 2

                    readonly property bool _netCost: section._netXp >= 0
                    readonly property color _netColor: _netCost ? Theme.accent : Theme.positive

                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: parent._netCost ? qsTr("NET BURDEN ON THE SOUL") : qsTr("NET GIFT TO THE SOUL")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.smallFont
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 2.0
                        horizontalAlignment: Text.AlignHCenter
                        color: parent._netColor
                        opacity: 0.85
                    }
                    Label {
                        Layout.fillWidth: true
                        // Sign-aware: prefix with + when the player has
                        // come out ahead (net cost is negative -- i.e.
                        // burdens > blessings). The display number is
                        // always positive magnitude.
                        text: (parent._netCost ? "" : "+") + Math.abs(section._netXp)
                        font.family: Theme.fontDisplay
                        font.pixelSize: 44
                        font.weight: Font.Bold
                        font.features: Theme.tabularNumbers
                        horizontalAlignment: Text.AlignHCenter
                        color: parent._netColor
                    }
                    Label {
                        Layout.fillWidth: true
                        text: parent._netCost ? qsTr("the cost of grace, after the gods take their due") : qsTr("favour earned by accepting hardship")
                        font.italic: true
                        font.pixelSize: Theme.smallFont
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.6
                        wrapMode: Text.WordWrap
                    }
                }

                Item {
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    Layout.topMargin: 8
                    Layout.bottomMargin: 8
                    Rectangle {
                        anchors.fill: parent
                        color: Theme.heading
                        opacity: 0.25
                    }
                }

                // Right pan -- XP granted by burdens. Uses Theme.highlight
                // (amber/gold) rather than the accent so the eye doesn't
                // confuse it with a "cost".
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1   // equal split; see banner note
                    Layout.alignment: Qt.AlignTop
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("GRANTED BY BURDENS")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.smallFont
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 2.0
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.highlight
                        opacity: 0.85
                    }
                    Label {
                        Layout.fillWidth: true
                        text: section._flawsXp
                        font.family: Theme.fontDisplay
                        font.pixelSize: 34
                        font.weight: Font.Bold
                        font.features: Theme.tabularNumbers
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.highlight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: section._flawsCap > 0 ? qsTr("of %1 the gods will recognise").arg(section._flawsCap) : qsTr("paid back for hardship accepted")
                        font.italic: true
                        font.pixelSize: Theme.smallFont
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.6
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // The Blessings register (福). Each merit is a card with a brush
    // kanji seal on the left, the merit name + subtype in body face,
    // the cost in Cinzel on the right rail, and a hover-revealed
    // ink-stroke "remove" handle. The "Inscribe" button at the foot
    // opens the catalogue dialog in merit mode.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Advantages")

        ColumnLayout {
            width: parent.width
            spacing: 10

            // Sub-caption + count, set as a margin note so the panel
            // title carries the section identity and this line carries
            // the inventory total.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8
                Label {
                    text: qsTr("blessings inscribed upon the soul")
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasMerits
                    // i18n note: prefer ngettext-style on the proxy side
                    // for proper pluralisation; this fallback keeps the
                    // line useful when the proxy doesn't supply one.
                    text: section._merits.length === 1 ? qsTr("1 blessing") : qsTr("%1 blessings").arg(section._merits.length)
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    opacity: 0.55
                }
            }

            // ---- Empty state ----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 170
                Layout.topMargin: 4
                visible: !section._hasMerits
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 90
                    Label {
                        anchors.centerIn: parent
                        text: "福"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.heading
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No favour has yet been claimed.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.titleFont
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Choose what gifts your samurai has been granted — " + "fortunes of birth, sworn allies, a sharp eye, a long memory.")
                    font.italic: true
                    font.pixelSize: Theme.bodyFont
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- List of merits -------------------------------------
            ListView {
                id: meritList
                visible: section._hasMerits
                Layout.fillWidth: true
                Layout.preferredHeight: contentHeight
                interactive: false
                spacing: 6
                model: section._merits

                delegate: PerkCard {
                    width: meritList.width
                    item: modelData
                    accentColor: Theme.secondary
                    kind: "merit"
                    onRemoveRequested: section._requestRemove(modelData)
                    onEditRequested: section._requestEdit(modelData, "merit")
                }
            }

            // ---- Inscribe button ------------------------------------
            // The add affordance is a quiet outlined block sitting flush
            // with the right edge -- it reads as a margin annotation
            // rather than a "BUY NOW" CTA, which fits the document
            // aesthetic.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: section._hasMerits ? 4 : 8
                spacing: 8
                Item {
                    Layout.fillWidth: true
                }
                AbstractButton {
                    id: inscribeMeritBtn
                    implicitHeight: 32
                    leftPadding: 14
                    rightPadding: 14
                    onClicked: section._openInscribe("merit")

                    background: Rectangle {
                        radius: 2
                        color: inscribeMeritBtn.down ? Theme.secondary : (inscribeMeritBtn.hovered ? Qt.rgba(0.224, 0.286, 0.671, 0.12) : "transparent")
                        border.color: Theme.secondary
                        border.width: 1
                    }
                    contentItem: RowLayout {
                        spacing: 8
                        Label {
                            text: "縁"
                            font.family: Theme.fontKanji
                            font.pixelSize: 20
                            color: inscribeMeritBtn.down ? Theme.parchmentBase : Theme.secondary
                        }
                        Label {
                            text: qsTr("Inscribe a Blessing")
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.smallFont + 1
                            font.weight: Font.DemiBold
                            font.letterSpacing: 1.4
                            color: inscribeMeritBtn.down ? Theme.parchmentBase : Theme.secondary
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // The Burdens register (禍). Same shape as Blessings but with the
    // crimson family of colours, the "禍" seal, a "+5 XP" stamp instead
    // of a cost figure (sign-flipped to read as a gift), and the cap
    // warning visible in the sub-caption when applicable.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Disadvantages")

        ColumnLayout {
            width: parent.width
            spacing: 10

            // Sub-caption + cap indicator. The cap is the soft 4e house
            // rule (typically 10 XP); a quiet right-aligned chip turns
            // amber when the player has approached the cap and crimson
            // when over it. We do not block over-cap entries -- some
            // tables ignore the cap; the UI just makes the state
            // visible.
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: 8

                Label {
                    text: qsTr("hardships sworn, gifts received")
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    opacity: 0.6
                }

                Item {
                    Layout.fillWidth: true
                }

                Rectangle {
                    visible: section._flawsCap > 0 && section._flaws.length > 0
                    Layout.preferredHeight: 18
                    implicitWidth: capLabel.implicitWidth + 14

                    readonly property bool _over: section._flawsXp > section._flawsCap
                    readonly property bool _near: !_over && section._flawsXp >= Math.floor(section._flawsCap * 0.8)

                    color: _over ? Theme.accent : (_near ? Theme.highlight : "transparent")
                    border.color: _over ? Theme.accentMuted : (_near ? Theme.highlight : Theme.borderSubtle)
                    border.width: 1
                    radius: 9
                    opacity: _over || _near ? 1.0 : 0.7

                    Label {
                        id: capLabel
                        anchors.centerIn: parent
                        text: qsTr("%1 / %2 XP").arg(section._flawsXp).arg(section._flawsCap)
                        font.family: Theme.fontDisplay
                        font.pixelSize: 10
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.2
                        font.features: Theme.tabularNumbers
                        color: parent._over || parent._near ? Theme.parchmentBase : Theme.ink
                        opacity: parent._over || parent._near ? 1.0 : 0.7
                    }
                }
            }

            // ---- Empty state ----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 170
                Layout.topMargin: 4
                visible: !section._hasFlaws
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 90
                    Label {
                        anchors.centerIn: parent
                        text: "禍"
                        font.family: Theme.fontKanji
                        font.pixelSize: 120
                        color: Theme.accent
                        opacity: 0.16
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No hardship has been sworn.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.titleFont
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("A samurai who accepts a flaw is granted experience to compensate. " + "Choose the burdens you carry, and the gods will balance the scale.")
                    font.italic: true
                    font.pixelSize: Theme.bodyFont
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- List of flaws --------------------------------------
            ListView {
                id: flawList
                visible: section._hasFlaws
                Layout.fillWidth: true
                Layout.preferredHeight: contentHeight
                interactive: false
                spacing: 6
                model: section._flaws

                delegate: PerkCard {
                    width: flawList.width
                    item: modelData
                    accentColor: Theme.accent
                    kind: "flaw"
                    onRemoveRequested: section._requestRemove(modelData)
                    onEditRequested: section._requestEdit(modelData, "flaw")
                }
            }

            // ---- Inscribe button ------------------------------------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: section._hasFlaws ? 4 : 8
                spacing: 8
                Item {
                    Layout.fillWidth: true
                }
                AbstractButton {
                    id: inscribeFlawBtn
                    implicitHeight: 32
                    leftPadding: 14
                    rightPadding: 14
                    onClicked: section._openInscribe("flaw")

                    background: Rectangle {
                        radius: 2
                        color: inscribeFlawBtn.down ? Theme.accent : (inscribeFlawBtn.hovered ? Qt.rgba(0.690, 0.188, 0.188, 0.12) : "transparent")
                        border.color: Theme.accent
                        border.width: 1
                    }
                    contentItem: RowLayout {
                        spacing: 8
                        Label {
                            text: "業"
                            font.family: Theme.fontKanji
                            font.pixelSize: 20
                            color: inscribeFlawBtn.down ? Theme.parchmentBase : Theme.accent
                        }
                        Label {
                            text: qsTr("Accept a Burden")
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.smallFont + 1
                            font.weight: Font.DemiBold
                            font.letterSpacing: 1.4
                            color: inscribeFlawBtn.down ? Theme.parchmentBase : Theme.accent
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Embedded picker dialog. The section keeps a single instance and
    // re-opens it in merit or flaw mode -- the dialog's catalogue and
    // accent colours flip on the `kind` property. Hosting it here (vs.
    // letting the controller spawn it) keeps the keyboard focus and
    // overlay parenting consistent with the rest of the QML sheet.
    // -----------------------------------------------------------------
    Dialogs.InscribePerkDialog {
        id: inscribeDlg
        // controller is expected to expose:
        //   appCtrl.availableMerits  -> [{ ruleId, name, suggestedCost,
        //                                  description, source, ranks }]
        //   appCtrl.availableFlaws   -> same shape
        //   appCtrl.inscribePerk(kind, ruleId, rank, overrideCost) -> void
    }

    // Edit dialog -- driven from the per-card edit button. The
    // proxy's PerkAdv exposes its handle as `advId`, which is what the
    // controller's editPerk slot looks up.
    Dialogs.EditPerkDialog {
        id: editDlg
    }

    // -----------------------------------------------------------------
    // Internal -- routes user actions either through the controller (if
    // the controller exposes the method) or the embedded dialog. The
    // double-dispatch lets the proxy author choose: a single
    // `openInscribe*` call (controller owns the dialog) OR the inline
    // dialog (proxy just provides catalogue properties).
    // -----------------------------------------------------------------
    function _openInscribe(kind) {
        if (appCtrl && kind === "merit" && appCtrl.openInscribeMerit) {
            appCtrl.openInscribeMerit();
            return;
        }
        if (appCtrl && kind === "flaw" && appCtrl.openInscribeFlaw) {
            appCtrl.openInscribeFlaw();
            return;
        }
        inscribeDlg.present(kind);
    }

    function _requestRemove(item) {
        if (!item)
            return;
        // Starting-school entries can't be refunded (they have no XP
        // cost on the stack); the card hides its remove control in that
        // case, so this guard is a belt-and-braces.
        if (item.isStarting)
            return;
        if (appCtrl && appCtrl.removePerk) {
            appCtrl.removePerk(item.advId);
        }
    }

    function _requestEdit(item, kind) {
        if (!item || item.isStarting)
            return;
        editDlg.present({
                "kind": kind,
                "advId": item.advId,
                "name": item.name,
                "category": item.category,
                "rank": item.rank,
                "cost": item.cost,
                "suggestedCost": item.suggestedCost,
                "subtype": item.subtype
            });
    }

    // =================================================================
    // PerkCard -- inline component used by both registers. Defined here
    // (rather than as a separate file) because it has no reuse outside
    // this section and keeping the parametrisation local makes the
    // accent-colour / kanji / kind handoff easy to follow.
    // =================================================================
    component PerkCard: Rectangle {
        id: card
        property var item: null
        property color accentColor: Theme.heading
        property string kind: "merit"   // "merit" | "flaw"

        signal removeRequested
        signal editRequested

        readonly property bool _isFlaw: kind === "flaw"
        readonly property bool _isStarting: !!(item && item.isStarting)
        readonly property bool _isCustom: !!(item && item.isCustom)
        readonly property int _cost: (item && item.cost !== undefined) ? item.cost : 0
        readonly property int _suggested: (item && item.suggestedCost !== undefined) ? item.suggestedCost : 0
        // Strikethrough is meaningful only when both figures exist and
        // disagree; suppressing it for the suggested==0 case avoids a
        // misleading "0̶ 5" reading on free-by-tag merits.
        readonly property bool _showStrike: _suggested > 0 && _suggested !== _cost && !_isStarting
        readonly property string _categoryText: (item && item.category && item.category.length > 0) ? item.category : ""
        readonly property bool _hasCategory: card._categoryText.length > 0
        readonly property bool _hasRank: !!(item && item.rank && item.rank > 0)
        readonly property string _subtypeText: (item && item.subtype && item.subtype.length > 0) ? item.subtype : ""
        readonly property bool _hasSubtitle: _isStarting || _subtypeText.length > 0

        implicitHeight: cardBody.implicitHeight + 18

        color: hoverHandler.hovered ? Theme.parchmentBase : Theme.parchmentInset
        border.color: hoverHandler.hovered ? Qt.darker(accentColor, 1.4) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color  {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color  {
            ColorAnimation {
                duration: 120
            }
        }

        // Left rail accent -- 3px crimson/indigo strip that turns the
        // rectangle into a "sealed scroll segment".
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: card.accentColor
            opacity: card._isStarting ? 0.45 : 0.9
        }

        HoverHandler {
            id: hoverHandler
        }

        RowLayout {
            id: cardBody
            anchors.fill: parent
            anchors.margins: 10
            anchors.leftMargin: 14
            spacing: 12

            // Body column -- title row carries name + category/rank pills;
            // the subtitle below shows the per-instance subtype (or, for
            // starting-school entries, the "granted by..." rationale).
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: (card.item && card.item.name) ? card.item.name : qsTr("(unnamed)")
                        font.pixelSize: Theme.bodyFont + 1
                        font.weight: Font.DemiBold
                        color: Theme.ink
                        elide: Text.ElideRight
                        Layout.alignment: Qt.AlignVCenter
                    }

                    // Category pill -- outlined, accent-tinted. Stays
                    // intrinsically sized so the title row stays packed
                    // to the left.
                    Rectangle {
                        visible: card._hasCategory
                        Layout.preferredHeight: 18
                        Layout.alignment: Qt.AlignVCenter
                        implicitWidth: categoryLabel.implicitWidth + 14
                        color: "transparent"
                        border.color: card.accentColor
                        border.width: 1
                        radius: 9
                        opacity: 0.75
                        Label {
                            id: categoryLabel
                            anchors.centerIn: parent
                            text: card._categoryText
                            font.family: Theme.fontDisplay
                            font.pixelSize: 10
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.2
                            color: card.accentColor
                        }
                    }

                    // Rank pill -- same shape as the category pill.
                    Rectangle {
                        visible: card._hasRank
                        Layout.preferredHeight: 18
                        Layout.alignment: Qt.AlignVCenter
                        implicitWidth: rankLabel.implicitWidth + 14
                        color: "transparent"
                        border.color: card.accentColor
                        border.width: 1
                        radius: 9
                        opacity: 0.75
                        Label {
                            id: rankLabel
                            anchors.centerIn: parent
                            text: qsTr("Rank %1").arg(card.item ? card.item.rank : 0)
                            font.family: Theme.fontDisplay
                            font.pixelSize: 10
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.2
                            color: card.accentColor
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                Label {
                    visible: card._hasSubtitle
                    Layout.fillWidth: true
                    text: card._isStarting ? qsTr("granted by your starting school") : card._subtypeText
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    color: Theme.ink
                    opacity: 0.6
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                }
            }

            // Cost column. Three stacked lines:
            //   - (conditional) suggestedCost in a small strikethrough --
            //     only when the actual cost was overridden and a
            //     rulebook figure exists, so the discount stays visible
            //     after the purchase.
            //   - actual cost in Cinzel; "+N" for flaws so the figure
            //     reads as a gift rather than a debit.
            //   - "XP" caption.
            ColumnLayout {
                Layout.preferredWidth: 70
                Layout.alignment: Qt.AlignVCenter
                spacing: 0

                Label {
                    visible: card._showStrike
                    Layout.fillWidth: true
                    // "suggested: 7" -- both the label and the figure
                    // carry the strikeout so the eye reads them as a
                    // single struck phrase rather than two glyphs that
                    // happen to share a line.
                    text: qsTr("suggested:") + " " + (card._isFlaw && card._suggested !== 0 ? "+" + card._suggested : "" + card._suggested)
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.smallFont
                    font.weight: Font.DemiBold
                    font.features: Theme.tabularNumbers
                    font.strikeout: true
                    horizontalAlignment: Text.AlignRight
                    color: Theme.ink
                    opacity: 0.45
                }
                Label {
                    Layout.fillWidth: true
                    text: card._isFlaw && card._cost !== 0 ? "+" + card._cost : card._cost
                    font.family: Theme.fontDisplay
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignRight
                    color: card._isFlaw ? Theme.highlight : card.accentColor
                    opacity: card._isStarting ? 0.5 : 1.0
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("XP")
                    font.family: Theme.fontDisplay
                    font.pixelSize: 9
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignRight
                    color: card._isFlaw ? Theme.highlight : card.accentColor
                    opacity: 0.8
                }
            }

            // Action handles -- edit pencil + remove cross. Both are
            // hover-revealed and disappear on starting-school entries
            // (which have no advancement stack entry to mutate). The
            // pair sits inside a fixed-width holder so the cost column
            // doesn't dance horizontally as cards gain/lose the hover
            // affordance.
            Item {
                Layout.preferredWidth: 50
                Layout.preferredHeight: 22
                Layout.alignment: Qt.AlignVCenter
                visible: !card._isStarting

                RowLayout {
                    anchors.fill: parent
                    spacing: 6

                    AbstractButton {
                        id: editBtn
                        visible: hoverHandler.hovered
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        Layout.alignment: Qt.AlignVCenter
                        onClicked: card.editRequested()

                        background: Rectangle {
                            radius: 11
                            color: editBtn.hovered ? card.accentColor : "transparent"
                            border.color: card.accentColor
                            border.width: 1
                            opacity: editBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity  {
                                NumberAnimation {
                                    duration: 120
                                }
                            }
                        }
                        contentItem: Label {
                            text: "✎"   // U+270E lower-right pencil
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: editBtn.hovered ? Theme.parchmentBase : card.accentColor
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: card._isFlaw ? qsTr("Edit this burden") : qsTr("Edit this blessing")
                    }

                    AbstractButton {
                        id: removeBtn
                        visible: hoverHandler.hovered
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        Layout.alignment: Qt.AlignVCenter
                        onClicked: card.removeRequested()

                        background: Rectangle {
                            radius: 11
                            color: removeBtn.hovered ? card.accentColor : "transparent"
                            border.color: card.accentColor
                            border.width: 1
                            opacity: removeBtn.hovered ? 1.0 : 0.55
                            Behavior on opacity  {
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
                            color: removeBtn.hovered ? Theme.parchmentBase : card.accentColor
                        }
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: card._isFlaw ? qsTr("Release this burden") : qsTr("Forfeit this blessing")
                    }
                }
            }
            // Mirror placeholder so the cost column lands at the same
            // x even on starting-school entries (which suppress the
            // action holder above).
            Item {
                visible: card._isStarting
                Layout.preferredWidth: 50
                Layout.preferredHeight: 22
            }
        }
    }
}
