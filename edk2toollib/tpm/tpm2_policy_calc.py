# @file tpm2_policy_calc.py
# This file contains classes used to calculate TPM 2.0 policies
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""A module containing classes used to calculate TPM 2.0 policies."""

import hashlib
import struct
from typing import Optional, Union

import edk2toollib.tpm.tpm2_defs as t2d

# ========================================================================================
##
# POLICY TREE CLASSES
# These are used to describe a final policy structure.
# You can construct nodes to form complex policies from the policy primitive classes.
##
# PolicyTreeOr                                 <--- Tree Node
# /          \
# PolicyTreeSolo         PolicyTreeAnd                     <--- Tree Nodes
# /                     /        \
# PolicyCommandCode     PolicyLocality    PolicyCommandCode         <--- Primitives
##
# ========================================================================================


class PolicyHasher(object):
    """An object used to hash TPM 2.0 policies with a specified hash."""

    def __init__(self, hash_type: str) -> "PolicyHasher":
        """Init the hasher with the specified hash.

        Args:
            hash_type (str): sha256 or sha384

        Raises:
            (ValueError): Invalid hash type
        """
        if hash_type not in ["sha256", "sha384"]:
            raise ValueError("Invalid hash type '%s'!" % hash_type)

        self.hash_type = hash_type
        self.hash_size = {"sha256": 32, "sha384": 48}[hash_type]

    def get_size(self) -> int:
        """Returns the size of the hash."""
        return self.hash_size

    def hash(self, data: str) -> bytes:
        """Hashes the data using the specified type."""
        hash_obj = None
        if self.hash_type == "sha256":
            hash_obj = hashlib.sha256()
        else:
            hash_obj = hashlib.sha384()

        hash_obj.update(data)

        return hash_obj.digest()


class PolicyCalculator(object):  # noqa
    def __init__(self, primitive_dict, policy_tree):  # noqa
        # For now, we'll leave this pretty sparse.
        # We should have WAY more testing for this stuff.
        self.primitive_dict = primitive_dict
        self.policy_tree = policy_tree

    def generate_digest(self, digest_type):  # noqa
        pass


class PolicyTreeOr(object):
    """Object representing an OR junction in a policy tree."""

    def __init__(self, components: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> "PolicyTreeOr":
        """Inits the policy tree junction with a list of connected components.

        Args:
            components (list): list of components

        Raises:
            (ValueError): More then 8 connections
        """
        # OR connections can only be 8 digests long.
        # They CAN, however, be links of ORs.
        if len(components) > 8:
            raise ValueError("OR junctions cannot contain more than 8 sub-policies!")

        self.components = components

    def get_type(self) -> str:
        """Returns the type of junction."""
        return "or"

    def validate(self) -> bool:
        """Validates all components have the correct attributes."""
        result = True

        for component in self.components:
            # All components must be convertible into a policy.
            if not hasattr(component, "get_policy"):
                result = False

            # All components must also be valid.
            if not hasattr(component, "validate") or not component.validate():
                result = False

        return result

    def get_policy_buffer(self, hash_obj: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> bytes:
        """Creates and returns a buffer representing the policy."""
        concat_policy_buffer = b"\x00" * hash_obj.get_size()
        concat_policy_buffer += struct.pack(">L", t2d.TPM_CC_PolicyOR)
        concat_policy_buffer += b"".join([component.get_policy(hash_obj) for component in self.components])
        return concat_policy_buffer

    def get_policy(self, hash_obj: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> int:
        """Returns a hashed policy buffer."""
        return hash_obj.hash(self.get_policy_buffer(hash_obj))


class PolicyTreeAnd(object):
    """Object representing an AND junction in a policy tree."""

    def __init__(self, components: list[Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]]) -> "PolicyTreeAnd":
        """Inits the policy tree junction with a list of connected components."""
        # ANDs must only be composed of primitives. For simplicity, I guess.
        # Honestly, this has spiralled out of control, but something is better than nothing.
        for component in components:
            if not hasattr(component, "get_buffer_for_digest"):
                raise ValueError("AND junctions must consist of primitives!")

        self.components = components

    def get_type(self) -> str:
        """Returns the type of junction."""
        return "and"

    def validate(self) -> bool:
        """Validate."""
        # Not sure why don't validate here instead of in the init?
        return True

    def get_policy(self, hash_obj: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> bytes:
        """Returns a hashed policy buffer."""
        current_digest = b"\x00" * hash_obj.get_size()
        for component in self.components:
            current_digest = hash_obj.hash(current_digest + component.get_buffer_for_digest())
        return current_digest


class PolicyTreeSolo(object):
    """This object should only be used to put a single policy claim under an OR."""

    def __init__(self, policy_obj: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> "PolicyTreeSolo":
        """Inits the policy tree junction."""
        if not hasattr(policy_obj, "get_buffer_for_digest"):
            raise ValueError("Supplied policy object is missing required functionality!")

        self.policy_obj = policy_obj

    def get_type(self) -> str:
        """Returns the type of junction."""
        return "solo"

    def validate(self) -> bool:
        """Validate."""
        # Not sure why don't validate here instead of in the init?
        return True

    def get_policy_buffer(self, hash_obj: Union["PolicyTreeAnd", "PolicyTreeOr", "PolicyTreeSolo"]) -> bytes:
        """Creates and returns a buffer representing the policy."""
        return (b"\x00" * hash_obj.get_size()) + self.policy_obj.get_buffer_for_digest()

    def get_policy(self, hash_obj: Union["PolicyTreeAnd", "PolicyTreeOr"]) -> int:
        """Returns a hashed policy buffer."""
        return hash_obj.hash(self.get_policy_buffer(hash_obj))


# ========================================================================================
##
# POLICY PRIMITIVES
# These classes are used to describe a single assertion (eg. PolicyLocality) and
# can be used with the PolicyTree classes to construct complex policies.
##
# ========================================================================================


class PolicyLocality(object):
    """Policy Primitive to describe a single assertion to create complex assertions."""

    def __init__(self, localities: list[int]) -> "PolicyLocality":
        """Init with the requested localities."""
        # Update the bitfield with the requested localities.
        if localities is not None:
            self.bitfield = self.calc_bitfield_from_list(localities)
        else:
            self.bitfield = 0b00000000

    def get_bitfield(self) -> int:
        """Return the bitfield attribute."""
        return self.bitfield

    def calc_bitfield_from_list(self, localities: list[int]) -> int:
        """Calculate the bitfield from a list of localities."""
        bitfield = 0b00000000

        # First, we need to validate all of the localities in the list.
        for value in localities:
            # If the value is in a bad range, we're done here.
            if not (0 <= value < 5) and not (32 <= value < 256):
                raise ValueError("Invalid locality '%d'!" % value)
            # An "upper" locality must be individual. Cannot combine with 0-4.
            if (32 <= value < 256) and len(localities) > 1:
                raise ValueError("Cannot combine locality '%d' with others!" % value)

        # If the list is empty... well, we're done.
        if len(localities) == 0:
            pass

        # Now, if we're an "upper" locality, that's a simple value.
        elif len(localities) == 1 and (32 <= localities[0] < 256):
            bitfield = localities[0]

        # We have to actually "think" to calculate the "lower" localities.
        else:
            for value in localities:
                bitfield |= 1 << value

        return bitfield

    def get_buffer_for_digest(self) -> str:
        r"""Serializes the primitive.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        # NOTE: We force big-endian to match the marshalling in the TPM.
        return struct.pack(">LB", t2d.TPM_CC_PolicyLocality, self.bitfield)


class PolicyCommandCode(object):
    """Policy Primitive to describe a Command code."""

    def __init__(self, command_code_string: Optional[str] = None) -> "PolicyCommandCode":
        """Init with the requested command code string."""
        # Check to make sure that a command_code can be found.
        str_command_code_string = str(command_code_string)
        command_code = t2d.CommandCode.get_code(str_command_code_string)
        if command_code is None:
            raise ValueError("Command code '%s' unknown!" % str_command_code_string)
        self.command_code_string = str_command_code_string

    def get_code(self) -> str:
        """Returns the command_code_string attribute."""
        return self.command_code_string

    def get_buffer_for_digest(self) -> str:
        r"""Serializes the primitive.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        # NOTE: We force big-endian to match the marshalling in the TPM.
        return struct.pack(
            ">LL",
            t2d.CommandCode.get_code("TPM_CC_PolicyCommandCode"),
            t2d.CommandCode.get_code(self.command_code_string),
        )
