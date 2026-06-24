// Copyright (C) 2014-2026 Daniele Simonetti
// Settings section (設 / "Configure"). A selective port of the legacy
// SettingsWidget: only the preferences that mean something on the
// parchment sheet -- localization, the Insight-calculation method, the
// PDF export flag -- plus the front-end switch. The QWidget-only chrome
// settings (table colours, app font, banner) are deliberately omitted.
//
// Bindings:
//   appSettings.availableLocales / insightMethods   -- option lists
//   appSettings.useSystemLocale / userLocale         -- localization
//   appSettings.insightCalculation                   -- applied at once
//   appSettings.firstPageSkills                      -- read at export
//   appSettings.useQmlUi                             -- front-end switch
// Setters: appSettings.setUseSystemLocale / setUserLocale /
//   setInsightCalculation / setFirstPageSkills / setUseQmlUi.
// Restart-required changes are surfaced via the MainSheet toast, driven
// by appSettings.reloadRequired.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: root
    spacing: Theme.s4

    // First matching index for `id` in a [{id, ...}] list, or -1.
    function indexOfId(list, id) {
        if (!list)
            return -1;
        for (var i = 0; i < list.length; ++i) {
            if (list[i].id === id)
                return i;
        }
        return -1;
    }

    // --- Language ----------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Language")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Use the system language")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RToggle {
                    checked: appSettings ? appSettings.useSystemLocale : true
                    onToggled: if (appSettings)
                        appSettings.setUseSystemLocale(checked)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Language")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RComboBox {
                    id: localeCombo
                    Layout.preferredWidth: 220
                    textRole: "name"
                    model: appSettings ? appSettings.availableLocales : []
                    enabled: appSettings ? !appSettings.useSystemLocale : false
                    // Read as disabled when the system language wins -- the
                    // skin keeps its parchment colours otherwise, so state
                    // would be conveyed by interactivity alone (§11).
                    opacity: enabled ? 1.0 : 0.45
                    Component.onCompleted: currentIndex = root.indexOfId(
                        model, appSettings ? appSettings.userLocale : "")
                    onActivated: function (i) {
                        if (appSettings && model[i])
                            appSettings.setUserLocale(model[i].id);
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Changing the language takes effect the next time you start the app.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }
        }
    }

    // --- Rules -------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Rules")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Insight calculation")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RComboBox {
                    id: insightCombo
                    Layout.preferredWidth: 260
                    textRole: "name"
                    model: appSettings ? appSettings.insightMethods : []
                    Component.onCompleted: currentIndex = root.indexOfId(
                        model, appSettings ? appSettings.insightCalculation : 1)
                    onActivated: function (i) {
                        if (appSettings && model[i])
                            appSettings.setInsightCalculation(model[i].id);
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Changes how your Insight Rank is worked out. Applies immediately.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                Layout.topMargin: Theme.s2
                Layout.bottomMargin: Theme.s2
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Free shopping")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RToggle {
                    checked: appSettings ? appSettings.buyForFree : false
                    onToggled: if (appSettings)
                        appSettings.setBuyForFree(checked)
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Buy advancements with no experience cost — an aid for "
                    + "GMs and quick builds. Affects new purchases only, and "
                    + "switches itself off when you restart the app.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }
        }
    }

    // --- Character sheet (PDF export) --------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Character Sheet")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Print skills on the first page")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RToggle {
                    checked: appSettings ? appSettings.firstPageSkills : false
                    onToggled: if (appSettings)
                        appSettings.setFirstPageSkills(checked)
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Used when you export your character sheet to PDF.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Theme.s2
                Label {
                    text: qsTr("Print the current Armor TN")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RToggle {
                    checked: appSettings ? appSettings.printCurrentArmorTn : false
                    onToggled: if (appSettings)
                        appSettings.setPrintCurrentArmorTn(checked)
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("The current Armor TN changes constantly during play; leave this off to print a blank field you can fill in by hand.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }
        }
    }

    // --- Interface (front-end switch) --------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Interface")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Text size")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RComboBox {
                    id: fontSizeCombo
                    Layout.preferredWidth: 260
                    textRole: "name"
                    model: appSettings ? appSettings.fontSizes : []
                    Component.onCompleted: currentIndex = root.indexOfId(
                        model, appSettings ? appSettings.fontSize : "standard")
                    onActivated: function (i) {
                        if (appSettings && model[i])
                            appSettings.setFontSize(model[i].id);
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Makes the sheet text larger and easier to read. Applies immediately.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                Layout.topMargin: Theme.s2
                Layout.bottomMargin: Theme.s2
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("Use the new interface")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsLabel
                    font.weight: Theme.wSemiBold
                    color: Theme.ink
                    Layout.fillWidth: true
                }
                Widgets.L5RToggle {
                    checked: appSettings ? appSettings.useQmlUi : true
                    onToggled: if (appSettings)
                        appSettings.setUseQmlUi(checked)
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Turn this off to return to the classic interface. Takes effect after a restart.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }
        }
    }
}
