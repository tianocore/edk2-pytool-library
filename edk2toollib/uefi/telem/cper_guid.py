# @file cper :.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

# TODO: Probably going to trash this as known guids will exist in the friendlynames.csv file

"""
/* ---Notify type GUIDs--- */

                  2dce8bb1-bdd7-450e-b9ad-9cf4ebd4f890
CMC_NOTIFY_TYPE : 2dce8bb1-bdd7-450e-b9ad-9cf4ebd4f890

CPE_NOTIFY_TYPE : 4e292f96-d843-4a55-a8c2-d481f27ebeee

MCE_NOTIFY_TYPE : e8f56ffe-919c-4cc5-ba88-65abe14913bb

PCIe_NOTIFY_TYPE : cf93c01f-1a16-4dfc-b8bc-9c4daf67c104

INIT_NOTIFY_TYPE : cc5263e8-9308-454a-89d0-340bd39bc98e

NMI_NOTIFY_TYPE : 5bad89ff-b7e6-42c9-814a-cf2485d6e98a

BOOT_NOTIFY_TYPE : 3d61a466-ab40-409a-a6-98-f3-62-d4-64-b3-8f

SEA_NOTIFY_TYPE : 9a78788a-bbe8-11e4-80-9e-67-61-1e-5d-46-b0

SEI_NOTIFY_TYPE : 5c284c81-b0ae-4e87-a3-22-b0-4c-85-62-43-23

PEI_NOTIFY_TYPE : 09a9D5ac-5204-4214-96-e5-94-99-2e-75-2b-cd

BMC_NOTIFY_TYPE : 487565ba-6494-4367-95-ca-4e-ff-89-35-22-f6

SCI_NOTIFY_TYPE : e9d59197-94ee-4a4f-8a-d8-9b-7d-8b-d9-3d-2e

EXTINT_NOTIFY_TYPE : fe84086e-b557-43cf-ac-1b-17-98-2e-07-84-70

DEVICE_DRIVER_NOTIFY_TYPE : 0033f803-2e70-4e88-99-2c-6f-26-da-f3-db-7a

CMCI_NOTIFY_TYPE : 919448b2-3739-4b7f-a8-f1-e0-06-28-05-c2-a3

/* ---Standard Error Section type GUIDs--- */

PROCESSOR_GENERIC_ERROR_SECTION : 9876ccad-47b4-4bdb-b6-5e-16-f1-93-c4-f3-db

DEVICE_DRIVER_ERROR_SECTION : 00000000-0000-0000-00-00-00-00-00-00-00-00

IPMI_MSR_DUMP_SECTION : 1c15b445-9b06-4667-ac-25-33-c0-56-b8-88-03

XPF_PROCESSOR_ERROR_SECTION : dc3ea0b0-a144-4797-b9-5b-53-fa-24-2b-6e-1d

IPF_PROCESSOR_ERROR_SECTION : e429faf1-3cb7-11d4-bc-a7-00-80-c7-3c-88-81

ARM_PROCESSOR_ERROR_SECTION : e19e3d16-bc11-11e4-9c-aa-c2-05-1d-5d-46-b0

MEMORY_ERROR_SECTION : a5bc1114-6f64-4ede-b8-63-3e-83-ed-7c-83-b1

PCIEXPRESS_ERROR_SECTION : d995e954-bbc1-430f-ad-91-b4-4d-cb-3c-6f-35

PCIXBUS_ERROR_SECTION : c5753963-3b84-4095-bf-78-ed-da-d3-f9-c9-dd

PCIXDEVICE_ERROR_SECTION : eb5e4685-ca66-4769-b6-a2-26-06-8b-00-13-26

FIRMWARE_ERROR_RECORD_REFERENCE : 81212a96-09ed-4996-94-71-8d-72-9c-8e-69-ed

PMEM_ERROR_SECTION : 81687003-dbfd-4728-9f-fd-f0-90-4f-97-59-7d

/* ---Processor check information type GUIDs--- */

WHEA_CACHECHECK : a55701f5-e3ef-43de-ac-72-24-9b-57-3f-ad-2c

WHEA_TLBCHECK : fc06b535-5e1f-4562-9f-25-0a-3b-9a-db-63-c3

WHEA_BUSCHECK : 1cf3f8b3-c5b1-49a2-aa-59-5e-ef-92-ff-a6-3c

WHEA_MSCHECK : 48ab7f57-dc34-4f6c-a7-d3-b0-b5-b0-a7-43-14

/*
Start of the Microsoft specific guids
*/

/* ---Microsoft record creator--- */

WHEA_RECORD_CREATOR : cf07c4bd-b789-4e18-b3-c4-1f-73-2c-b5-71-31

/* ---Microsoft specific notification types--- */

GENERIC_NOTIFY_TYPE : 3e62a467-ab40-409a-a6-98-f3-62-d4-64-b3-8f

/* ---Microsoft specific error section types--- */

IPF_SAL_RECORD_SECTION : 6f3380d1-6eb0-497f-a5-78-4d-4c-65-a7-16-17

XPF_MCA_SECTION : 8a1e1d01-42f9-4557-9c-33-56-5e-5c-c3-f7-e8

NMI_SECTION : e71254e7-c1b9-4940-ab-76-90-97-03-a4-32-0f

GENERIC_SECTION : e71254e8-c1b9-4940-ab-76-90-97-03-a4-32-0f

WHEA_ERROR_PACKET_SECTION : e71254e9-c1b9-4940-ab-76-90-97-03-a4-32-0f
"""
