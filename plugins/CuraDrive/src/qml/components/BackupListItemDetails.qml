// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ColumnLayout
{
    id: backupDetails
    width: parent.width
    spacing: 10 * screenScaleFactor
    property var backupDetailsData

    // Cura version
    BackupListItemDetailsRow
    {
        iconSource: "../images/cura.svg"
        label: catalog.i18nc("@backuplist:label", "Cura Version")
        value: backupDetailsData.metadata.cura_release
    }

    // Machine count.
    BackupListItemDetailsRow
    {
        iconSource: "../images/printer.svg"
        label: catalog.i18nc("@backuplist:label", "Machines")
        value: backupDetailsData.metadata.machine_count
    }

    // Meterial count.
    BackupListItemDetailsRow
    {
        iconSource: "../images/material.svg"
        label: catalog.i18nc("@backuplist:label", "Materials")
        value: backupDetailsData.metadata.material_count
    }

    // Meterial count.
    BackupListItemDetailsRow
    {
        iconSource: "../images/profile.svg"
        label: catalog.i18nc("@backuplist:label", "Profiles")
        value: backupDetailsData.metadata.profile_count
    }

    // Meterial count.
    BackupListItemDetailsRow
    {
        iconSource: "../images/plugin.svg"
        label: catalog.i18nc("@backuplist:label", "Plugins")
        value: backupDetailsData.metadata.plugin_count
    }

    // Spacer.
    Item
    {
        width: parent.width
        height: 10 * screenScaleFactor
    }
}
