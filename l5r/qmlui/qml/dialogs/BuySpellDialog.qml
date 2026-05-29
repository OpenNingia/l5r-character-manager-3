// Copyright (C) 2014-2026 Daniele Simonetti
// BuySpellDialog -- QML-native catalogue picker for learning a spell
// free-form. Replaces the freeform mode of the legacy QWidget
// SpellAdvDialog (l5r/dialogs/spelldlg.py) without reusing any of its
// widgets. Opened from SpellsSection:
//     buySpellDlg.present()
// (The entrypoint is `present` rather than `open` so it does not shadow
// Dialog's built-in open(), which present() calls to pop the modal up.)
//
// A two-pane brushed scroll, kakemono-aspect (taller than wide). The
// left column is the catalogue of not-yet-known spells, filterable by
// element and by name; each row carries an element-colour dot and a
// mastery tag, and spells beyond the caster's present reach are dimmed
// so the eye is drawn to what can actually be inscribed. The right
// column is the chosen spell's detail: an element chip + mastery pill +
// (when the school grants an elemental leaning) an affinity/deficiency
// chip, the casting line (range / area of effect / duration / raises),
// the prose, then a single requirement -- the mastery the caster can
// presently reach, measured against the spell's mastery. Learning a
// free-form spell costs no experience, so there is no XP plaque; the
// Learn button enables only when the spell is within reach, gating
// exactly as the legacy SpellAdvDialog gated its Finish button
// (is_learnable: Insight Rank, adjusted by affinity/deficiency,
// must meet the spell's mastery).
//
// Catalogue entry shape (from appCtrl.availableSpellsToBuy()):
//   { id, name,
//     element:      "fire",        // ring key, or "multi"/"dragon"
//     elementLabel: "Fire",        // multi -> "Air, Fire"
//     mastery:      3,
//     masteryMod:   1,             // affinity(+) / deficiency(-)
//     range, area, duration,       // casting line
//     raises:       "Range, Area",
//     tags:         ["attack"],
//     source:       "Core p.182",
//     description:  "...",
//     reach:        4,             // highest mastery the caster can learn
//     eligible:     true }
// On accept the dialog calls appCtrl.learnSpell(id).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property var _catalogue: []
    property var _selected: null
    property string _search: ""
    property string _elementFilter: ""    // "" == every element
    // Tag constraint. _tagMode is "all" (no constraint), "only" (keep
    // spells carrying _tagKey) or "hide" (drop spells carrying _tagKey).
    // The default option set always offers a "Hide Maho" entry so the
    // forbidden blood-magic spells can be kept out of sight, mirroring
    // the legacy dialog's Allow / No / Only Maho radios.
    property string _tagMode: "all"
    property string _tagKey: ""

    // --- derived --------------------------------------------------
    // Learning a spell is a blessing / cultivation -> the blue accent
    // family, matching BuySkillDialog / BuyKataDialog. The per-spell
    // element hue is data shown in the detail pane, not the dialog's
    // identity.
    readonly property color _accent: Theme.secondary
    readonly property color _accentSoft: Qt.lighter(Theme.secondary, 1.7)
    readonly property bool _eligible: !!(_selected && _selected.eligible)

    // The element filter options. "multi" / "dragon" sit outside the
    // five-ring palette and are coloured gold by _ringColorFor().
    readonly property var _elementOptions: [
        { key: "",      label: qsTr("All Elements") },
        { key: "earth", label: qsTr("Earth") },
        { key: "air",   label: qsTr("Air") },
        { key: "water", label: qsTr("Water") },
        { key: "fire",  label: qsTr("Fire") },
        { key: "void",  label: qsTr("Void") },
        { key: "multi", label: qsTr("Multi-Element") },
        { key: "dragon", label: qsTr("Dragon") }
    ]

    // Tag filter options, derived from whatever tags the catalogue
    // actually carries. Always opens with "All Tags" and a dedicated
    // "Hide Maho" exclusion; every distinct tag then follows as a
    // "show only" entry (so picking "Maho" shows only maho spells).
    readonly property var _tagOptions: {
        var opts = [
            { key: "", mode: "all", label: qsTr("All Tags") },
            { key: "maho", mode: "hide", label: qsTr("Hide Maho") }
        ];
        var seen = ({});
        var tags = [];
        for (var i = 0; i < _catalogue.length; ++i) {
            var t = _catalogue[i].tags || [];
            for (var j = 0; j < t.length; ++j) {
                var key = t[j];
                if (key && !seen[key]) {
                    seen[key] = true;
                    tags.push(key);
                }
            }
        }
        tags.sort();
        for (var k = 0; k < tags.length; ++k)
            opts.push({ key: tags[k], mode: "only", label: tags[k].charAt(0).toUpperCase() + tags[k].slice(1) });
        return opts;
    }

    // Ring hue for a spell's element, or gold for multi/dragon spells
    // (which fall outside the §2.3 ring palette).
    function _ringColorFor(key) {
        if (key === "earth" || key === "air" || key === "water" || key === "fire" || key === "void")
            return Theme.ringColor(key);
        return Theme.heading;
    }

    function _hasTag(rec, key) {
        var t = (rec && rec.tags) ? rec.tags : [];
        for (var i = 0; i < t.length; ++i)
            if (t[i] === key)
                return true;
        return false;
    }

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "呪"
    title: qsTr("Learn a Spell")
    tagline: qsTr("a spell is yours to inscribe only when your understanding runs deep enough")
    accent: _accent
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Learn")
    acceptGlyph: "呪"
    acceptEnabled: dlg._eligible
    statusText: {
        if (!dlg._selected)
            return "";
        if (dlg._eligible)
            return qsTr("This spell is within your reach — inscribe it into your library at no cost.");
        return dlg._reasonFor(dlg._selected);
    }
    onAccepted: {
        if (dlg._selected && dlg._eligible && appCtrl)
            appCtrl.learnSpell(dlg._selected.id);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._refreshCatalogue();
        dlg._selected = null;
        dlg._search = "";
        dlg._elementFilter = "";
        dlg._tagMode = "all";
        dlg._tagKey = "";
        tagCombo.currentIndex = 0;
        dlg.open();
    }

    function _refreshCatalogue() {
        dlg._catalogue = (appCtrl && appCtrl.availableSpellsToBuy) ? (appCtrl.availableSpellsToBuy() || []) : [];
    }

    function _filteredCatalogue() {
        var needle = (dlg._search || "").toLowerCase();
        var elem = dlg._elementFilter;
        var out = [];
        for (var i = 0; i < dlg._catalogue.length; ++i) {
            var c = dlg._catalogue[i];
            if (elem.length > 0 && c.element !== elem)
                continue;
            if (dlg._tagMode === "hide" && dlg._hasTag(c, dlg._tagKey))
                continue;
            if (dlg._tagMode === "only" && !dlg._hasTag(c, dlg._tagKey))
                continue;
            if (needle.length > 0 && (!c.name || c.name.toLowerCase().indexOf(needle) < 0))
                continue;
            out.push(c);
        }
        return out;
    }

    // One short sentence on why a spell can't yet be learned -- the
    // mastery-reach gate (the only freeform gate the legacy dialog set).
    function _reasonFor(s) {
        if (!s)
            return "";
        return qsTr("Your understanding reaches Mastery %1 — this spell is Mastery %2.").arg(s.reach).arg(s.mastery);
    }

    padding: Theme.s1   // thin inset so the opaque two-pane body reveals the gold frame

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // FILTER BAND -- element dropdown + search field, spanning both
        // panes.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentInset
            implicitHeight: filterRow.implicitHeight + 16
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

                Widgets.L5RComboBox {
                    id: elementCombo
                    Layout.preferredWidth: 160
                    textRole: "label"
                    model: dlg._elementOptions
                    accent: dlg._accent
                    onActivated: function (index) {
                        var opt = dlg._elementOptions[index];
                        dlg._elementFilter = opt ? opt.key : "";
                    }
                }

                Widgets.L5RComboBox {
                    id: tagCombo
                    Layout.preferredWidth: 160
                    textRole: "label"
                    model: dlg._tagOptions
                    accent: dlg._accent
                    onActivated: function (index) {
                        var opt = dlg._tagOptions[index];
                        dlg._tagMode = opt ? opt.mode : "all";
                        dlg._tagKey = opt ? opt.key : "";
                    }
                }

                Widgets.L5RSearchField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholder: qsTr("seek a spell by name…")
                    onTextChanged: dlg._search = text
                }
            }
        }

        // =============================================================
        // The body row -- catalogue list, divider, detail pane.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // =========================================================
            // LEFT PANE -- the catalogue list.
            // =========================================================
            Pane {
                id: catalogPane
                Layout.fillHeight: true
                Layout.preferredWidth: 320
                padding: 0
                background: Rectangle {
                    color: Theme.parchmentSidebar
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase

                ListView {
                    id: catalogView
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
                        implicitHeight: 46
                        readonly property bool _active: dlg._selected && dlg._selected.id === modelData.id
                        readonly property bool _eligible: !!modelData.eligible
                        readonly property color _ringColor: dlg._ringColorFor(modelData.element || "void")

                        onClicked: dlg._selected = modelData

                        background: Rectangle {
                            color: row._active ? dlg._accentSoft : (row.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.04) : "transparent")
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: row._active ? 3 : 0
                                color: dlg._accent
                            }
                        }

                        contentItem: RowLayout {
                            anchors.fill: parent
                            spacing: 8

                            // Element dot -- colour-codes the spell's Ring.
                            Rectangle {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 8
                                implicitHeight: 8
                                radius: 4
                                color: row._ringColor
                                opacity: row._eligible ? 1.0 : 0.4
                            }
                            Label {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                verticalAlignment: Text.AlignVCenter
                                text: modelData.name || qsTr("(unnamed)")
                                font.pixelSize: Theme.fsBody
                                font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                color: Theme.ink
                                opacity: row._eligible ? 1.0 : 0.5
                                elide: Text.ElideRight
                            }
                            // Mastery tag.
                            Label {
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                text: qsTr("M%1").arg(modelData.mastery || 0)
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsStatSmall
                                font.features: Theme.tabularNumbers
                                color: row._ringColor
                                opacity: row._eligible ? 0.95 : 0.45
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: catalogView.count === 0
                        text: dlg._catalogue.length === 0 ? qsTr("every spell is already known") : qsTr("nothing matches that brushstroke")
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.55
                    }
                }
            }

            // =========================================================
            // VERTICAL DIVIDER.
            // =========================================================
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // =========================================================
            // RIGHT PANE -- the chosen spell's detail.
            // =========================================================
            Pane {
                id: detailPane
                Layout.fillWidth: true
                Layout.fillHeight: true
                padding: 0
                background: Rectangle {
                    color: Theme.parchment
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase
                palette.alternateBase: Theme.parchmentInset
                palette.placeholderText: Theme.inkFaint
                palette.buttonText: Theme.ink

                readonly property color _ringColor: dlg._selected ? dlg._ringColorFor(dlg._selected.element || "void") : Theme.accent

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
                        text: "呪"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a spell from the register at your left.")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsHeading1
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
                        text: qsTr("Dimmed spells lie beyond your present understanding — advance your Insight, or deepen the affinity your school grants, to bring them within reach.")
                        font.italic: true
                        font.pixelSize: Theme.fsBody
                        color: Theme.ink
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

                    // Title.
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
                        color: detailPane._ringColor
                        opacity: 0.5
                    }

                    // Meta row -- element chip + mastery pill + affinity
                    // chip + source.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        readonly property int _mod: dlg._selected ? (dlg._selected.masteryMod || 0) : 0

                        // Element chip -- filled in the Ring's hue.
                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: elementLabel.implicitWidth + 18
                            radius: 10
                            color: detailPane._ringColor
                            Label {
                                id: elementLabel
                                anchors.centerIn: parent
                                text: dlg._selected ? (dlg._selected.elementLabel || "").toUpperCase() : ""
                                font.family: Theme.fontDisplay
                                font.pixelSize: 10
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.4
                                color: Theme.whiteWash
                            }
                        }
                        // Mastery pill -- outlined in the Ring's hue.
                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: masteryLabel.implicitWidth + 18
                            color: "transparent"
                            border.color: detailPane._ringColor
                            border.width: 1
                            radius: 10
                            opacity: 0.85
                            Label {
                                id: masteryLabel
                                anchors.centerIn: parent
                                text: qsTr("Mastery %1").arg(dlg._selected ? (dlg._selected.mastery || 0) : 0)
                                font.family: Theme.fontDisplay
                                font.pixelSize: 10
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: detailPane._ringColor
                            }
                        }
                        // Affinity / deficiency chip -- the school's
                        // elemental leaning toward this spell. Positive
                        // (affinity) in success-green, negative
                        // (deficiency) in crimson; absent when neutral.
                        Rectangle {
                            visible: parent._mod !== 0
                            Layout.preferredHeight: 20
                            implicitWidth: modLabel.implicitWidth + 16
                            radius: 10
                            color: "transparent"
                            border.width: 1
                            border.color: parent._mod > 0 ? Theme.positive : Theme.accent
                            opacity: 0.9
                            Label {
                                id: modLabel
                                anchors.centerIn: parent
                                text: parent.parent._mod > 0 ? qsTr("AFFINITY +%1").arg(parent.parent._mod) : qsTr("DEFICIENCY %1").arg(parent.parent._mod)
                                font.family: Theme.fontDisplay
                                font.pixelSize: 10
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: parent.parent._mod > 0 ? Theme.positive : Theme.accent
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: dlg._selected && dlg._selected.source
                            text: dlg._selected ? dlg._selected.source : ""
                            font.italic: true
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.55
                        }
                    }

                    // Casting line -- range / area / duration / raises.
                    // Only the fields the datapack fills in are shown.
                    Flow {
                        Layout.fillWidth: true
                        spacing: 18

                        Repeater {
                            model: dlg._selected ? [
                                { k: qsTr("RANGE"), v: dlg._selected.range || "" },
                                { k: qsTr("AREA"), v: dlg._selected.area || "" },
                                { k: qsTr("DURATION"), v: dlg._selected.duration || "" },
                                { k: qsTr("RAISES"), v: dlg._selected.raises || "" }
                            ] : []
                            delegate: ColumnLayout {
                                visible: (modelData.v || "").length > 0
                                spacing: 0
                                Label {
                                    text: modelData.k
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: 9
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

                    // Description -- scrolls if long; the requirement
                    // stays pinned below.
                    ScrollView {
                        id: descScroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        Label {
                            width: descScroll.availableWidth
                            text: dlg._selected && dlg._selected.description ? dlg._selected.description : qsTr("No description provided in the datapack.")
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: Theme.ink
                        }
                    }

                    // =====================================================
                    // WHAT IT REQUIRES -- the mastery-reach gate. This is
                    // the heart of the dialog: it shows the player exactly
                    // why a spell is or isn't within reach. (Free-form
                    // spells cost no XP, so there is no price plaque.)
                    // =====================================================
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: demandsBody.implicitHeight + 22
                        color: Theme.parchmentInset
                        border.color: dlg._eligible ? Theme.borderSubtle : Theme.accent
                        border.width: dlg._eligible ? 1 : 1.5
                        radius: 2

                        Behavior on border.color {
                            ColorAnimation {
                                duration: 160
                            }
                        }

                        ColumnLayout {
                            id: demandsBody
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("WHAT IT REQUIRES")
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsCaption
                                font.weight: Theme.headingWeight
                                font.letterSpacing: 2.0
                                color: Theme.heading
                                opacity: 0.9
                            }

                            // Mastery-reach gate line.
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Label {
                                    text: dlg._eligible ? "✓" : "✕"
                                    font.pixelSize: Theme.fsBody
                                    color: dlg._eligible ? Theme.positive : Theme.accent
                                    Layout.preferredWidth: 14
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: dlg._selected ? qsTr("Mastery %1 — your understanding presently reaches Mastery %2").arg(dlg._selected.mastery || 0).arg(dlg._selected.reach || 0) : ""
                                    font.pixelSize: Theme.fsBody
                                    color: Theme.ink
                                    opacity: dlg._eligible ? 0.9 : 1.0
                                    wrapMode: Text.WordWrap
                                }
                            }

                            // Tags -- shown here as a quiet footnote, since
                            // they refine eligibility for school grants but
                            // not free-form learning.
                            Flow {
                                Layout.fillWidth: true
                                visible: dlg._selected && dlg._selected.tags && dlg._selected.tags.length > 0
                                spacing: 6

                                Repeater {
                                    model: dlg._selected && dlg._selected.tags ? dlg._selected.tags : []
                                    delegate: Rectangle {
                                        implicitHeight: 18
                                        implicitWidth: tagLabel.implicitWidth + 14
                                        radius: 9
                                        color: "transparent"
                                        border.width: 1
                                        border.color: Theme.borderSubtle
                                        Label {
                                            id: tagLabel
                                            anchors.centerIn: parent
                                            text: (modelData || "").toUpperCase()
                                            font.family: Theme.fontDisplay
                                            font.pixelSize: 9
                                            font.weight: Theme.wSemiBold
                                            font.letterSpacing: 1.0
                                            color: Theme.inkMuted
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }   // body RowLayout
    }
}
