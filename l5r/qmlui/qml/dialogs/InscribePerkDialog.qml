// Copyright (C) 2014-2026 Daniele Simonetti
// InscribePerkDialog -- QML-native catalogue picker for advantages /
// disadvantages. The dialog is mode-flipped at present() time:
//     inscribeDlg.present("merit")   // browse advantages
//     inscribeDlg.present("flaw")    // browse disadvantages
// (The custom entrypoint is `present` rather than `open` so it does not
// shadow Dialog's built-in `open()` method, which we still call from
// inside present() to actually pop the modal up.)
// The catalogue is read from the controller. Each catalogue entry
// looks like:
//   { ruleId:        "allies",
//     name:          "Allies",
//     suggestedCost: 4,                 // for the default rank
//     description:   "...",
//     source:        "Core p.155",
//     subtypeLabel:  "ally name",       // optional, drives a freeform field
//     ranks: [ { rank: 1, cost: 1 },    // optional; rankless if absent
//              { rank: 2, cost: 2 },
//              { rank: 3, cost: 4 },
//              { rank: 4, cost: 7 },
//              { rank: 5, cost: 9 } ] }
// The dialog calls appCtrl.inscribePerk(kind, ruleId, rank, subtype,
// overrideCost) on accept. `overrideCost` is -1 when the suggested
// cost is to be used; any non-negative number is the player's manual
// value. This sign convention is deliberate -- it keeps the controller
// from needing a separate "use suggested" boolean and survives in the
// advancement record as a positive integer.
// Aesthetic: a two-pane brushed scroll, kakemono-aspect (taller than
// wide). Left column = the catalogue, with a search bar at its head.
// Right column = the chosen entry's detail, the rank picker (if any),
// an optional subtype field, and the SUGGESTED-XP plaque. Beneath the
// plaque a quiet "Override the suggested cost" switch flips the plaque
// into an editable field; when the override is on, the plaque becomes
// a crimson-rimmed inkwell so the deviation from rulebook reads at a
// glance.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Dialog {
    id: dlg
    parent: Overlay.overlay
    anchors.centerIn: Overlay.overlay
    modal: true
    standardButtons: Dialog.NoButton
    closePolicy: Popup.CloseOnEscape

    // --- mode + selection state -----------------------------------
    property string kind: "merit"   // "merit" | "flaw"
    property var _catalogue: []
    property var _categories: []        // [{id, name}], from appCtrl.perkCategories()
    property string _activeCategory: ""    // "" = all
    property var _selected: null
    property int _selectedRank: 1
    property string _subtype: ""
    property bool _overrideOn: false
    property int _overrideCost: 0
    property string _search: ""

    // --- derived ---------------------------------------------------
    readonly property bool _isFlaw: dlg.kind === "flaw"
    readonly property color _accent: _isFlaw ? Theme.accent : Theme.secondary
    readonly property color _accentSoft: _isFlaw ? Theme.accentSoft : Qt.lighter(Theme.secondary, 1.7)
    readonly property string _seal: _isFlaw ? "業" : "縁"

    readonly property int _suggestedCost: {
        if (!_selected)
            return 0;
        if (_selected.ranks && _selected.ranks.length > 0) {
            for (var i = 0; i < _selected.ranks.length; ++i) {
                if (_selected.ranks[i].rank === _selectedRank) {
                    return _selected.ranks[i].cost;
                }
            }
            return _selected.ranks[0].cost;
        }
        return _selected.suggestedCost || 0;
    }

    readonly property int _effectiveCost: _overrideOn ? _overrideCost : _suggestedCost

    // --- size: kakemono proportions, capped to the overlay --------
    // Taller than wide, like a hanging scroll. Capped so the dialog
    // doesn't outgrow the window on narrow desks.
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    title: _isFlaw ? qsTr("Accept a Burden") : qsTr("Inscribe a Blessing")

    // --- entrypoint -----------------------------------------------
    // Note: named `present` rather than `open` so it does not shadow
    // Dialog's own `open()` (a QML method on the parent type); the last
    // line below calls that built-in to actually display the modal.
    function present(kindArg) {
        dlg.kind = kindArg || "merit";
        dlg._refreshCatalogue();
        dlg._refreshCategories();
        dlg._activeCategory = "";
        dlg._selected = null;
        dlg._selectedRank = 1;
        dlg._subtype = "";
        dlg._overrideOn = false;
        dlg._overrideCost = 0;
        dlg._search = "";
        dlg.open();
    }

    function _refreshCatalogue() {
        if (!appCtrl) {
            dlg._catalogue = [];
            return;
        }
        // availableMerits/Flaws are @Slots on the controller, so they
        // must be invoked as functions; this also re-hits the data
        // layer so mid-session datapack imports are reflected.
        var src = _isFlaw ? appCtrl.availableFlaws() : appCtrl.availableMerits();
        dlg._catalogue = src || [];
    }

    function _refreshCategories() {
        if (!appCtrl || !appCtrl.perkCategories) {
            dlg._categories = [];
            return;
        }
        dlg._categories = appCtrl.perkCategories() || [];
    }

    function _filteredCatalogue() {
        var hasCat = dlg._activeCategory && dlg._activeCategory.length > 0;
        var hasSearch = dlg._search && dlg._search.length > 0;
        if (!hasCat && !hasSearch)
            return dlg._catalogue;
        var needle = hasSearch ? dlg._search.toLowerCase() : "";
        var out = [];
        for (var i = 0; i < dlg._catalogue.length; ++i) {
            var c = dlg._catalogue[i];
            if (hasCat && c.type !== dlg._activeCategory)
                continue;
            if (hasSearch && (!c.name || c.name.toLowerCase().indexOf(needle) < 0))
                continue;
            out.push(c);
        }
        return out;
    }

    function _accept() {
        if (!_selected)
            return;
        if (appCtrl && appCtrl.inscribePerk) {
            appCtrl.inscribePerk(dlg.kind, _selected.ruleId, _selectedRank, _subtype, _overrideOn ? _overrideCost : -1);
        }
        dlg.accept();
    }

    // --- backplate ------------------------------------------------
    background: Rectangle {
        color: Theme.parchment
        border.color: Theme.borderStrong
        border.width: 1
        radius: 2
        // Same fibre overlay the MainSheet uses, so the dialog reads
        // as a page lifted off the document rather than a flat card.
        Widgets.RicePaperOverlay {
        }
    }

    // The Dialog's default header is plain; replace it with a kakemono
    // banner that carries the brush seal and the title in Cinzel.
    header: Item {
        implicitHeight: 64
        Rectangle {
            anchors.fill: parent
            color: dlg._accentSoft
            opacity: 0.55
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: dlg._accent
            opacity: 0.45
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 14

            Label {
                text: dlg._seal
                font.family: Theme.fontKanji
                font.pixelSize: 42
                color: dlg._accent
                opacity: 0.88
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    text: dlg.title
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.titleFont + 2
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.6
                    color: Theme.heading
                }
                Label {
                    text: dlg._isFlaw ? qsTr("the gods weigh hardship and return the difference in experience") : qsTr("choose a gift to inscribe into your samurai's chronicle")
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    color: Theme.ink
                    opacity: 0.7
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // FILTER BAND -- a single full-width row spanning both panes,
        // sitting above the catalogue/detail split. Magnifier-led
        // search field on the left, category ComboBox on the right.
        // The ComboBox is hand-skinned to match the parchment surface
        // (same vocabulary as RankStepper: cream fill, hairline border,
        // brown text) -- the default platform ComboBox chrome fights
        // the document feel of the rest of the dialog.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentInset
            implicitHeight: filterRow.implicitHeight + 16
            // Bottom rule so the band reads as its own zone.
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.heading
                opacity: 0.3
            }
            RowLayout {
                id: filterRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                // Search slug -- magnifier + TextField, fillWidth so it
                // claims everything the combo doesn't.
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label {
                        text: "⌕"
                        font.pixelSize: 16
                        color: Theme.heading
                        opacity: 0.6
                    }
                    TextField {
                        id: searchField
                        Layout.fillWidth: true
                        placeholderText: dlg._isFlaw ? qsTr("seek a hardship by name…") : qsTr("seek a blessing by name…")
                        background: Item {
                        }   // dissolve into the inkwell
                        font.pixelSize: Theme.bodyFont
                        font.italic: text.length === 0
                        color: Theme.ink
                        placeholderTextColor: "#8a7a65"
                        onTextChanged: dlg._search = text
                    }
                }

                // Category combo -- hand-skinned to the parchment
                // vocabulary. `currentIndex` is bound to the source-of-
                // truth `_activeCategory`, so present() resetting it to
                // "" snaps the combo to "All categories" automatically.
                ComboBox {
                    id: categoryCombo
                    Layout.preferredWidth: 220
                    visible: dlg._categories.length > 0
                    textRole: "name"
                    // Sentinel "" id = no category filter; prepended
                    // so the player can always return to the unfiltered
                    // view from inside the combo without a separate
                    // "clear" affordance.
                    model: [{
                            "id": "",
                            "name": qsTr("All categories")
                        }].concat(dlg._categories)
                    currentIndex: {
                        var arr = categoryCombo.model;
                        for (var i = 0; i < arr.length; ++i) {
                            if (arr[i].id === dlg._activeCategory)
                                return i;
                        }
                        return 0;
                    }
                    onActivated: function (index) {
                        var rec = categoryCombo.model[index];
                        dlg._activeCategory = rec ? rec.id : "";
                    }

                    // --- closed-state skin ----------------------------
                    // Mirrors the RankStepper pill: cream fill (#fbf6e8),
                    // hairline subtle border, radius 3. 28px tall so the
                    // combo lines up with the search field's ascent.
                    background: Rectangle {
                        color: "#fbf6e8"
                        border.color: categoryCombo.activeFocus ? dlg._accent : Theme.borderSubtle
                        border.width: 1
                        radius: 3
                        implicitHeight: 28
                    }
                    contentItem: Label {
                        leftPadding: 10
                        rightPadding: categoryCombo.indicator.width + 6
                        text: categoryCombo.displayText
                        font.pixelSize: Theme.bodyFont
                        font.weight: Font.DemiBold
                        color: "#3a3a3a"
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    // Caret -- a small brushy ▾, brown to match the
                    // stepper button glyphs. Replaces the OS pixmap.
                    indicator: Label {
                        x: categoryCombo.width - width - 8
                        y: (categoryCombo.height - height) / 2
                        text: "▾"
                        font.pixelSize: 12
                        color: "#6b5b3f"
                        opacity: categoryCombo.pressed ? 1.0 : 0.85
                    }

                    // --- open-state popup ----------------------------
                    // The dropdown panel sits on the parchment palette
                    // so it never flashes a stock white plate against
                    // the cream page. Item rows are styled in the
                    // delegate below.
                    popup: Popup {
                        y: categoryCombo.height
                        width: categoryCombo.width
                        implicitHeight: contentItem.implicitHeight + 4
                        padding: 2
                        background: Rectangle {
                            color: Theme.parchmentBase
                            border.color: Theme.borderStrong
                            border.width: 1
                            radius: 3
                        }
                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: categoryCombo.popup.visible ? categoryCombo.delegateModel : null
                            currentIndex: categoryCombo.highlightedIndex
                            ScrollIndicator.vertical: ScrollIndicator {
                            }
                        }
                    }
                    delegate: ItemDelegate {
                        width: categoryCombo.width
                        implicitHeight: 26
                        highlighted: categoryCombo.highlightedIndex === index
                        background: Rectangle {
                            color: highlighted ? Qt.rgba(0.690, 0.188, 0.188, 0.12) : "transparent"
                        }
                        contentItem: Label {
                            leftPadding: 10
                            rightPadding: 6
                            text: modelData.name
                            font.pixelSize: Theme.bodyFont
                            color: "#3a3a3a"
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }

        // =============================================================
        // The body row -- catalogue list on the left, divider, detail
        // pane on the right. Sat under the filter band so the band's
        // bottom rule reads as the divider between filter and content.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // =========================================================
            // LEFT PANE -- the catalogue list (filter UI lives above).
            // =========================================================
            Pane {
                id: catalogPane
                Layout.fillHeight: true
                Layout.preferredWidth: 320
                padding: 0
                background: Rectangle {
                    color: Theme.parchmentSidebar
                    radius: 0
                    Widgets.RicePaperOverlay {
                    }
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase

                ListView {
                    id: catalogView
                    // Pane is a Control, not a Layout -- Layout attached
                    // properties wouldn't propagate, so we fill via
                    // anchors against the Pane's implicit content slot.
                    anchors.fill: parent
                    clip: true
                    model: dlg._filteredCatalogue()
                    spacing: 0
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: AbstractButton {
                        id: row
                        width: catalogView.width
                        implicitHeight: 44
                        readonly property bool _active: dlg._selected && dlg._selected.ruleId === modelData.ruleId

                        onClicked: {
                            dlg._selected = modelData;
                            // Reset rank/override when picking a fresh
                            // entry, otherwise the right pane carries
                            // stale state across rows.
                            if (modelData.ranks && modelData.ranks.length > 0) {
                                dlg._selectedRank = modelData.ranks[0].rank;
                            } else {
                                dlg._selectedRank = 1;
                            }
                            dlg._subtype = "";
                            dlg._overrideCost = dlg._suggestedCost;
                            // No-fixed-cost rules force the manual path
                            // straight away -- mirrors the Edit dialog so
                            // the player isn't faced with a 0 XP plaque
                            // and a locked switch.
                            dlg._overrideOn = dlg._suggestedCost === 0;
                        }

                        background: Rectangle {
                            color: row._active ? dlg._accentSoft : (row.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.04) : "transparent")
                            // Active row has a left-edge accent stripe.
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: row._active ? 3 : 0
                                color: dlg._accent
                            }
                        }
                        contentItem: Label {
                            anchors.fill: parent
                            anchors.leftMargin: row._active ? 14 : 12
                            anchors.rightMargin: 12
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.name || qsTr("(unnamed)")
                            font.pixelSize: Theme.bodyFont
                            font.weight: row._active ? Font.DemiBold : Font.Normal
                            color: Theme.ink
                            elide: Text.ElideRight
                        }
                    }

                    // Empty-search state.
                    Label {
                        anchors.centerIn: parent
                        visible: catalogView.count === 0
                        text: qsTr("nothing matches that brushstroke")
                        font.italic: true
                        font.pixelSize: Theme.smallFont
                        opacity: 0.55
                    }
                }
            }

            // =========================================================
            // VERTICAL DIVIDER -- thin ink rule between the panes.
            // =========================================================
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // =========================================================
            // RIGHT PANE -- the chosen entry's detail + the price scroll.
            // =========================================================
            Pane {
                id: detailPane
                Layout.fillWidth: true
                Layout.fillHeight: true
                padding: 0
                background: Rectangle {
                    color: Theme.parchment
                    radius: 0
                    Widgets.RicePaperOverlay {
                    }
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase
                palette.alternateBase: Theme.parchmentInset
                palette.placeholderText: "#8a7a65"
                palette.buttonText: Theme.ink

                // ---- Unselected state ----------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    visible: dlg._selected === null
                    spacing: 4

                    Item {
                        Layout.fillHeight: true
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: dlg._seal
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: dlg._isFlaw ? qsTr("Choose a hardship from the register at your left.") : qsTr("Choose a gift from the register at your left.")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.titleFont
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.4
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        Layout.maximumWidth: 380
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("The rulebook will suggest the proper cost; you may override it " + "if your table has agreed to a different price.")
                        font.italic: true
                        font.pixelSize: Theme.bodyFont
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.7
                        wrapMode: Text.WordWrap
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }

                // ---- Selected state ------------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    visible: dlg._selected !== null
                    spacing: 10

                    // Title block -- name in Cinzel, then a hairline rule.
                    Label {
                        Layout.fillWidth: true
                        text: dlg._selected ? dlg._selected.name : ""
                        font.family: Theme.fontDisplay
                        font.pixelSize: 22
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.0
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: dlg._accent
                        opacity: 0.4
                    }

                    // Source citation -- quiet, italic, right-aligned. The
                    // book reference often matters when the GM is checking
                    // the cost is correct, so it stays visible.
                    Label {
                        Layout.fillWidth: true
                        visible: dlg._selected && dlg._selected.source
                        horizontalAlignment: Text.AlignRight
                        text: dlg._selected ? dlg._selected.source : ""
                        font.italic: true
                        font.pixelSize: Theme.smallFont
                        opacity: 0.55
                    }

                    // Description -- scrolls if long; the price scroll at
                    // the bottom of the pane stays pinned. The Label width
                    // is bound to ScrollView.availableWidth (not parent.width
                    // -- inside a ScrollView `parent` is the internal
                    // content item, which has no defined width and would
                    // silently break word-wrap). contentWidth pins the
                    // horizontal extent so the scroll only travels
                    // vertically.
                    ScrollView {
                        id: descScroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        Label {
                            width: descScroll.availableWidth
                            text: dlg._selected && dlg._selected.description ? dlg._selected.description : qsTr("No description provided in the datapack.")
                            font.pixelSize: Theme.bodyFont
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: Theme.ink
                        }
                    }

                    // Rank picker -- only if the entry has multiple ranks.
                    // `Flow` rather than `RowLayout` so high-rank entries
                    // (Wealthy has 12+ ranks in some packs) wrap to a
                    // second line instead of overflowing the right pane.
                    // The leading "Rank" label is aligned to the top of
                    // the Flow so it stays put when the pills wrap.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: dlg._selected && dlg._selected.ranks && dlg._selected.ranks.length > 1
                        spacing: 10
                        Label {
                            text: qsTr("Rank")
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.smallFont
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.6
                            color: Theme.heading
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 6
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            Repeater {
                                model: dlg._selected && dlg._selected.ranks ? dlg._selected.ranks : []
                                delegate: AbstractButton {
                                    id: rankPip
                                    readonly property bool _active: dlg._selectedRank === modelData.rank
                                    implicitWidth: 36
                                    implicitHeight: 28
                                    onClicked: {
                                        dlg._selectedRank = modelData.rank;
                                        if (!dlg._overrideOn) {
                                            dlg._overrideCost = dlg._suggestedCost;
                                        }
                                    }
                                    background: Rectangle {
                                        radius: 2
                                        color: rankPip._active ? dlg._accent : (rankPip.hovered ? dlg._accentSoft : "transparent")
                                        border.color: rankPip._active ? dlg._accent : Theme.borderSubtle
                                        border.width: 1
                                        Behavior on color  {
                                            ColorAnimation {
                                                duration: 100
                                            }
                                        }
                                    }
                                    contentItem: Label {
                                        anchors.fill: parent
                                        text: modelData.rank
                                        font.family: Theme.fontDisplay
                                        font.pixelSize: Theme.bodyFont
                                        font.weight: Font.DemiBold
                                        font.features: Theme.tabularNumbers
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: rankPip._active ? Theme.parchmentBase : Theme.ink
                                    }
                                }
                            }
                        }
                    }

                    // Notes -- a freeform line for the per-instance detail
                    // (the "Yasuki Trading" of an Ally, the "broken arm" of
                    // a Bad Fortune). Stored in PerkAdv.extra. Universally
                    // present rather than per-rule because the legacy data
                    // pack does not flag which rules expect a subtype --
                    // any merit/flaw can carry a player note.
                    RowLayout {
                        Layout.fillWidth: true
                        visible: dlg._selected !== null
                        spacing: 10
                        Label {
                            text: qsTr("Notes")
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.smallFont
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.6
                            color: Theme.heading
                            Layout.preferredWidth: 110
                        }
                        TextField {
                            id: subtypeField
                            Layout.fillWidth: true
                            text: dlg._subtype
                            onTextEdited: dlg._subtype = text
                            placeholderText: dlg._isFlaw ? qsTr("circumstance, target, or detail…") : qsTr("name, ally, or detail…")
                            color: Theme.ink
                            placeholderTextColor: "#8a7a65"
                            background: Rectangle {
                                color: Theme.parchmentBase
                                border.color: Theme.borderSubtle
                                border.width: 1
                                radius: 2
                            }
                        }
                    }

                    // =====================================================
                    // The PRICE SCROLL -- the heart of the dialog. This is
                    // where the player sees what the rulebook suggests and
                    // decides whether to override. Visually it sits on its
                    // own raised inset so it reads as a separate "stamp".
                    // =====================================================
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: priceBody.implicitHeight + 22

                        color: dlg._overrideOn ? Qt.rgba(0.690, 0.188, 0.188, 0.05) : Theme.parchmentInset
                        border.color: dlg._overrideOn ? Theme.accent : Theme.borderSubtle
                        border.width: dlg._overrideOn ? 1.5 : 1
                        radius: 2

                        Behavior on color  {
                            ColorAnimation {
                                duration: 160
                            }
                        }
                        Behavior on border.color  {
                            ColorAnimation {
                                duration: 160
                            }
                        }
                        Behavior on border.width  {
                            NumberAnimation {
                                duration: 160
                            }
                        }

                        ColumnLayout {
                            id: priceBody
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            // Top row -- "SUGGESTED" caption + the figure.
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                // Caption column.
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0
                                    Label {
                                        text: dlg._overrideOn ? qsTr("MANUAL COST") : qsTr("SUGGESTED BY THE RULEBOOK")
                                        font.family: Theme.fontDisplay
                                        font.pixelSize: Theme.smallFont
                                        font.weight: Theme.headingWeight
                                        font.letterSpacing: 2.0
                                        color: dlg._overrideOn ? Theme.accent : Theme.heading
                                        opacity: 0.9
                                    }
                                    Label {
                                        text: dlg._isFlaw ? qsTr("experience the gods will grant in return") : qsTr("experience the chronicle will require")
                                        font.italic: true
                                        font.pixelSize: Theme.smallFont
                                        opacity: 0.6
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }

                                // Figure column. When the override is off
                                // this is a Cinzel plaque; when on, a
                                // SpinBox styled to feel like an inkwell.
                                Item {
                                    Layout.preferredWidth: 130
                                    Layout.preferredHeight: 56

                                    // The plaque (suggested mode).
                                    Rectangle {
                                        anchors.fill: parent
                                        visible: !dlg._overrideOn
                                        color: Theme.parchmentBase
                                        border.color: Theme.heading
                                        border.width: 1
                                        radius: 2
                                        Label {
                                            anchors.centerIn: parent
                                            text: (dlg._isFlaw ? "+" : "") + dlg._suggestedCost
                                            font.family: Theme.fontDisplay
                                            font.pixelSize: 32
                                            font.weight: Font.Bold
                                            font.features: Theme.tabularNumbers
                                            color: dlg._isFlaw ? Theme.highlight : dlg._accent
                                        }
                                        Label {
                                            anchors.bottom: parent.bottom
                                            anchors.right: parent.right
                                            anchors.bottomMargin: 4
                                            anchors.rightMargin: 6
                                            text: qsTr("XP")
                                            font.family: Theme.fontDisplay
                                            font.pixelSize: 9
                                            font.weight: Theme.headingWeight
                                            font.letterSpacing: 2.0
                                            color: dlg._isFlaw ? Theme.highlight : dlg._accent
                                            opacity: 0.7
                                        }
                                    }

                                    // The inkwell (override mode).
                                    SpinBox {
                                        id: overrideSpin
                                        anchors.fill: parent
                                        visible: dlg._overrideOn
                                        from: 0
                                        to: 999
                                        value: dlg._overrideCost
                                        editable: true
                                        onValueModified: dlg._overrideCost = value

                                        background: Rectangle {
                                            color: Theme.parchmentBase
                                            border.color: Theme.accent
                                            border.width: 1
                                            radius: 2
                                        }
                                        contentItem: TextInput {
                                            text: overrideSpin.textFromValue(overrideSpin.value, overrideSpin.locale)
                                            font.family: Theme.fontDisplay
                                            font.pixelSize: 28
                                            font.weight: Font.Bold
                                            font.features: Theme.tabularNumbers
                                            color: Theme.accent
                                            horizontalAlignment: TextInput.AlignHCenter
                                            verticalAlignment: TextInput.AlignVCenter
                                            readOnly: !overrideSpin.editable
                                            validator: overrideSpin.validator
                                            inputMethodHints: Qt.ImhFormattedNumbersOnly
                                            onTextEdited: {
                                                var v = parseInt(text);
                                                if (!isNaN(v)) {
                                                    overrideSpin.value = v;
                                                    dlg._overrideCost = v;
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // Override toggle -- a quiet switch + a one-line
                            // explanation. Deliberately understated so the
                            // suggested-cost path remains the default.
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.topMargin: 2
                                spacing: 10

                                Switch {
                                    id: overrideSwitch
                                    checked: dlg._overrideOn
                                    // Disable when the rule has no fixed
                                    // cost: the manual SpinBox is the only
                                    // valid input, so the toggle would be
                                    // meaningless. Matches EditPerkDialog.
                                    enabled: dlg._suggestedCost > 0
                                    onToggled: {
                                        dlg._overrideOn = checked;
                                        if (checked) {
                                            // Seed the override field with
                                            // the suggested value so the
                                            // player can adjust from a known
                                            // starting point instead of from
                                            // zero.
                                            dlg._overrideCost = dlg._suggestedCost;
                                            overrideSpin.value = dlg._suggestedCost;
                                        }
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: dlg._suggestedCost === 0
                                        ? qsTr("This rule has no fixed cost; set one manually.")
                                        : (dlg._overrideOn ? qsTr("Manual cost — agreed with your GM.")
                                                           : qsTr("Override the suggested cost"))
                                    font.pixelSize: Theme.bodyFont
                                    font.italic: !dlg._overrideOn
                                    color: dlg._overrideOn ? Theme.accent : Theme.ink
                                    opacity: dlg._overrideOn ? 1.0 : 0.7
                                    wrapMode: Text.WordWrap
                                }
                                // "Reset" appears only when overriding and
                                // the figure has drifted from the suggestion;
                                // it's a one-tap return to the rulebook.
                                AbstractButton {
                                    id: resetBtn
                                    visible: dlg._overrideOn && dlg._overrideCost !== dlg._suggestedCost
                                    onClicked: {
                                        dlg._overrideCost = dlg._suggestedCost;
                                        overrideSpin.value = dlg._suggestedCost;
                                    }
                                    implicitHeight: 22
                                    leftPadding: 8
                                    rightPadding: 8
                                    background: Rectangle {
                                        radius: 11
                                        color: resetBtn.hovered ? Theme.heading : "transparent"
                                        border.color: Theme.heading
                                        border.width: 1
                                        opacity: resetBtn.hovered ? 0.9 : 0.6
                                    }
                                    contentItem: Label {
                                        text: qsTr("reset to %1").arg(dlg._suggestedCost)
                                        font.family: Theme.fontDisplay
                                        font.pixelSize: 10
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 1.2
                                        color: resetBtn.hovered ? Theme.parchmentBase : Theme.heading
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }   // body RowLayout
    }

    // --- footer -- Cancel / Inscribe ------------------------------
    footer: Rectangle {
        implicitHeight: 56
        color: Theme.parchmentSidebar
        Widgets.RicePaperOverlay {
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Theme.heading
            opacity: 0.35
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 10

            // A quiet recap on the left so the player can read the
            // verdict without flicking their eyes back up to the plaque.
            Label {
                Layout.fillWidth: true
                visible: dlg._selected !== null
                text: dlg._isFlaw ? qsTr("This burden will grant +%1 XP.").arg(dlg._effectiveCost) : qsTr("This blessing will require %1 XP.").arg(dlg._effectiveCost)
                font.italic: true
                font.pixelSize: Theme.bodyFont
                color: dlg._overrideOn ? Theme.accent : Theme.ink
                opacity: dlg._overrideOn ? 1.0 : 0.75
                wrapMode: Text.WordWrap
            }
            Item {
                visible: dlg._selected === null
                Layout.fillWidth: true
            }

            AbstractButton {
                id: cancelBtn
                implicitHeight: 32
                leftPadding: 18
                rightPadding: 18
                onClicked: dlg.reject()
                background: Rectangle {
                    radius: 2
                    color: cancelBtn.down ? Qt.darker(Theme.parchmentBase, 1.05) : (cancelBtn.hovered ? Theme.parchmentBase : "transparent")
                    border.color: Theme.borderStrong
                    border.width: 1
                }
                contentItem: Label {
                    text: qsTr("Cancel")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.smallFont + 1
                    font.weight: Font.DemiBold
                    font.letterSpacing: 1.3
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            AbstractButton {
                id: inscribeBtn
                implicitHeight: 32
                leftPadding: 22
                rightPadding: 22
                enabled: dlg._selected !== null
                opacity: enabled ? 1.0 : 0.45
                onClicked: dlg._accept()

                background: Rectangle {
                    radius: 2
                    color: inscribeBtn.down ? Qt.darker(dlg._accent, 1.25) : dlg._accent
                    border.color: Qt.darker(dlg._accent, 1.4)
                    border.width: 1
                }
                contentItem: RowLayout {
                    spacing: 6
                    Label {
                        text: dlg._seal
                        font.family: Theme.fontKanji
                        font.pixelSize: 16
                        color: Theme.parchmentBase
                        opacity: 0.95
                    }
                    Label {
                        text: dlg._isFlaw ? qsTr("Accept") : qsTr("Inscribe")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.smallFont + 1
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1.6
                        color: Theme.parchmentBase
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
