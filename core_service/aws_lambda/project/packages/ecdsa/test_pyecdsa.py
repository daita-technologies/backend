from __future__ import with_statement, division

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
import sys
import shutil
import subprocess
import pytest
from binascii import hexlify, unhexlify
from hashlib import sha1, sha256, sha384, sha512
import hashlib
from functools import partial

from hypothesis import given
import hypothesis.strategies as st

from six import b, print_, binary_type
from .keys import SigningKey, VerifyingKey
from .keys import BadSignatureError, MalformedPointError, BadDigestError
from . import util
from .util import sigencode_der, sigencode_strings
from .util import sigdecode_der, sigdecode_strings
from .util import number_to_string, encoded_oid_ecPublicKey, MalformedSignature
from .curves import Curve, UnknownCurveError
from .curves import (
    SECP112r1,
    SECP112r2,
    SECP128r1,
    SECP160r1,
    NIST192p,
    NIST224p,
    NIST256p,
    NIST384p,
    NIST521p,
    SECP256k1,
    BRAINPOOLP160r1,
    BRAINPOOLP192r1,
    BRAINPOOLP224r1,
    BRAINPOOLP256r1,
    BRAINPOOLP320r1,
    BRAINPOOLP384r1,
    BRAINPOOLP512r1,
    curves,
)
from .ecdsa import (
    curve_brainpoolp224r1,
    curve_brainpoolp256r1,
    curve_brainpoolp384r1,
    curve_brainpoolp512r1,
)
from .ellipticcurve import Point
from . import der
from . import rfc6979
from . import ecdsa


class SubprocessError(Exception):
    pass


def run_openssl(cmd):
    OPENSSL = "openssl"
    p = subprocess.Popen(
        [OPENSSL] + cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, ignored = p.communicate()
    if p.returncode != 0:
        raise SubprocessError(
            "cmd '%s %s' failed: rc=%s, stdout/err was %s"
            % (OPENSSL, cmd, p.returncode, stdout)
        )
    return stdout.decode()


class ECDSA(unittest.TestCase):
    def test_basic(self):
        priv = SigningKey.generate()
        pub = priv.get_verifying_key()

        data = b("blahblah")
        sig = priv.sign(data)

        self.assertTrue(pub.verify(sig, data))
        self.assertRaises(BadSignatureError, pub.verify, sig, data + b("bad"))

        pub2 = VerifyingKey.from_string(pub.to_string())
        self.assertTrue(pub2.verify(sig, data))

    def test_deterministic(self):
        data = b("blahblah")
        secexp = int("9d0219792467d7d37b4d43298a7d0c05", 16)

        priv = SigningKey.from_secret_exponent(secexp, SECP256k1, sha256)
        pub = priv.get_verifying_key()

        k = rfc6979.generate_k(
            SECP256k1.generator.order(), secexp, sha256, sha256(data).digest()
        )

        sig1 = priv.sign(data, k=k)
        self.assertTrue(pub.verify(sig1, data))

        sig2 = priv.sign(data, k=k)
        self.assertTrue(pub.verify(sig2, data))

        sig3 = priv.sign_deterministic(data, sha256)
        self.assertTrue(pub.verify(sig3, data))

        self.assertEqual(sig1, sig2)
        self.assertEqual(sig1, sig3)

    def test_bad_usage(self):
        # sk=SigningKey() is wrong
        self.assertRaises(TypeError, SigningKey)
        self.assertRaises(TypeError, VerifyingKey)

    def test_lengths(self):
        default = NIST192p
        priv = SigningKey.generate()
        pub = priv.get_verifying_key()
        self.assertEqual(len(pub.to_string()), default.verifying_key_length)
        sig = priv.sign(b("data"))
        self.assertEqual(len(sig), default.signature_length)
        for curve in (
            NIST192p,
            NIST224p,
            NIST256p,
            NIST384p,
            NIST521p,
            BRAINPOOLP160r1,
            BRAINPOOLP192r1,
            BRAINPOOLP224r1,
            BRAINPOOLP256r1,
            BRAINPOOLP320r1,
            BRAINPOOLP384r1,
            BRAINPOOLP512r1,
        ):
            priv = SigningKey.generate(curve=curve)
            pub1 = priv.get_verifying_key()
            pub2 = VerifyingKey.from_string(pub1.to_string(), curve)
            self.assertEqual(pub1.to_string(), pub2.to_string())
            self.assertEqual(len(pub1.to_string()), curve.verifying_key_length)
            sig = priv.sign(b("data"))
            self.assertEqual(len(sig), curve.signature_length)

    def test_serialize(self):
        seed = b("secret")
        curve = NIST192p
        secexp1 = util.randrange_from_seed__trytryagain(seed, curve.order)
        secexp2 = util.randrange_from_seed__trytryagain(seed, curve.order)
        self.assertEqual(secexp1, secexp2)
        priv1 = SigningKey.from_secret_exponent(secexp1, curve)
        priv2 = SigningKey.from_secret_exponent(secexp2, curve)
        self.assertEqual(hexlify(priv1.to_string()), hexlify(priv2.to_string()))
        self.assertEqual(priv1.to_pem(), priv2.to_pem())
        pub1 = priv1.get_verifying_key()
        pub2 = priv2.get_verifying_key()
        data = b("data")
        sig1 = priv1.sign(data)
        sig2 = priv2.sign(data)
        self.assertTrue(pub1.verify(sig1, data))
        self.assertTrue(pub2.verify(sig1, data))
        self.assertTrue(pub1.verify(sig2, data))
        self.assertTrue(pub2.verify(sig2, data))
        self.assertEqual(hexlify(pub1.to_string()), hexlify(pub2.to_string()))

    def test_nonrandom(self):
        s = b("all the entropy in the entire world, compressed into one line")

        def not_much_entropy(numbytes):
            return s[:numbytes]

        # we control the entropy source, these two keys should be identical:
        priv1 = SigningKey.generate(entropy=not_much_entropy)
        priv2 = SigningKey.generate(entropy=not_much_entropy)
        self.assertEqual(
            hexlify(priv1.get_verifying_key().to_string()),
            hexlify(priv2.get_verifying_key().to_string()),
        )
        # likewise, signatures should be identical. Obviously you'd never
        # want to do this with keys you care about, because the secrecy of
        # the private key depends upon using different random numbers for
        # each signature
        sig1 = priv1.sign(b("data"), entropy=not_much_entropy)
        sig2 = priv2.sign(b("data"), entropy=not_much_entropy)
        self.assertEqual(hexlify(sig1), hexlify(sig2))

    def assertTruePrivkeysEqual(self, priv1, priv2):
        self.assertEqual(
            priv1.privkey.secret_multiplier, priv2.privkey.secret_multiplier
        )
        self.assertEqual(
            priv1.privkey.public_key.generator,
            priv2.privkey.public_key.generator,
        )

    def test_privkey_creation(self):
        s = b("all the entropy in the entire world, compressed into one line")

        def not_much_entropy(numbytes):
            return s[:numbytes]

        priv1 = SigningKey.generate()
        self.assertEqual(priv1.baselen, NIST192p.baselen)

        priv1 = SigningKey.generate(curve=NIST224p)
        self.assertEqual(priv1.baselen, NIST224p.baselen)

        priv1 = SigningKey.generate(entropy=not_much_entropy)
        self.assertEqual(priv1.baselen, NIST192p.baselen)
        priv2 = SigningKey.generate(entropy=not_much_entropy)
        self.assertEqual(priv2.baselen, NIST192p.baselen)
        self.assertTruePrivkeysEqual(priv1, priv2)

        priv1 = SigningKey.from_secret_exponent(secexp=3)
        self.assertEqual(priv1.baselen, NIST192p.baselen)
        priv2 = SigningKey.from_secret_exponent(secexp=3)
        self.assertTruePrivkeysEqual(priv1, priv2)

        priv1 = SigningKey.from_secret_exponent(secexp=4, curve=NIST224p)
        self.assertEqual(priv1.baselen, NIST224p.baselen)

    def test_privkey_strings(self):
        priv1 = SigningKey.generate()
        s1 = priv1.to_string()
        self.assertEqual(type(s1), binary_type)
        self.assertEqual(len(s1), NIST192p.baselen)
        priv2 = SigningKey.from_string(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

        s1 = priv1.to_pem()
        self.assertEqual(type(s1), binary_type)
        self.assertTrue(s1.startswith(b("-----BEGIN EC PRIVATE KEY-----")))
        self.assertTrue(s1.strip().endswith(b("-----END EC PRIVATE KEY-----")))
        priv2 = SigningKey.from_pem(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

        s1 = priv1.to_der()
        self.assertEqual(type(s1), binary_type)
        priv2 = SigningKey.from_der(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

        priv1 = SigningKey.generate(curve=NIST256p)
        s1 = priv1.to_pem()
        self.assertEqual(type(s1), binary_type)
        self.assertTrue(s1.startswith(b("-----BEGIN EC PRIVATE KEY-----")))
        self.assertTrue(s1.strip().endswith(b("-----END EC PRIVATE KEY-----")))
        priv2 = SigningKey.from_pem(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

        s1 = priv1.to_der()
        self.assertEqual(type(s1), binary_type)
        priv2 = SigningKey.from_der(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

    def test_privkey_strings_brainpool(self):
        priv1 = SigningKey.generate(curve=BRAINPOOLP512r1)
        s1 = priv1.to_pem()
        self.assertEqual(type(s1), binary_type)
        self.assertTrue(s1.startswith(b("-----BEGIN EC PRIVATE KEY-----")))
        self.assertTrue(s1.strip().endswith(b("-----END EC PRIVATE KEY-----")))
        priv2 = SigningKey.from_pem(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

        s1 = priv1.to_der()
        self.assertEqual(type(s1), binary_type)
        priv2 = SigningKey.from_der(s1)
        self.assertTruePrivkeysEqual(priv1, priv2)

    def assertTruePubkeysEqual(self, pub1, pub2):
        self.assertEqual(pub1.pubkey.point, pub2.pubkey.point)
        self.assertEqual(pub1.pubkey.generator, pub2.pubkey.generator)
        self.assertEqual(pub1.curve, pub2.curve)

    def test_pubkey_strings(self):
        priv1 = SigningKey.generate()
        pub1 = priv1.get_verifying_key()
        s1 = pub1.to_string()
        self.assertEqual(type(s1), binary_type)
        self.assertEqual(len(s1), NIST192p.verifying_key_length)
        pub2 = VerifyingKey.from_string(s1)
        self.assertTruePubkeysEqual(pub1, pub2)

        priv1 = SigningKey.generate(curve=NIST256p)
        pub1 = priv1.get_verifying_key()
        s1 = pub1.to_string()
        self.assertEqual(type(s1), binary_type)
        self.assertEqual(len(s1), NIST256p.verifying_key_length)
        pub2 = VerifyingKey.from_string(s1, curve=NIST256p)
        self.assertTruePubkeysEqual(pub1, pub2)

        pub1_der = pub1.to_der()
        self.assertEqual(type(pub1_der), binary_type)
        pub2 = VerifyingKey.from_der(pub1_der)
        self.assertTruePubkeysEqual(pub1, pub2)

        self.assertRaises(
            der.UnexpectedDER, VerifyingKey.from_der, pub1_der + b("junk")
        )
        badpub = VerifyingKey.from_der(pub1_der)

        class FakeGenerator:
            def order(self):
                return 123456789

        class FakeCurveFp:
            def p(self):
                return int(
                    "6525534529039240705020950546962731340"
                    "4541085228058844382513856749047873406763"
                )

        badcurve = Curve(
            "unknown", FakeCurveFp(), FakeGenerator(), (1, 2, 3, 4, 5, 6), None
        )
        badpub.curve = badcurve
        badder = badpub.to_der()
        self.assertRaises(UnknownCurveError, VerifyingKey.from_der, badder)

        pem = pub1.to_pem()
        self.assertEqual(type(pem), binary_type)
        self.assertTrue(pem.startswith(b("-----BEGIN PUBLIC KEY-----")), pem)
        self.assertTrue(pem.strip().endswith(b("-----END PUBLIC KEY-----")), pem)
        pub2 = VerifyingKey.from_pem(pem)
        self.assertTruePubkeysEqual(pub1, pub2)

    def test_pubkey_strings_brainpool(self):
        priv1 = SigningKey.generate(curve=BRAINPOOLP512r1)
        pub1 = priv1.get_verifying_key()
        s1 = pub1.to_string()
        self.assertEqual(type(s1), binary_type)
        self.assertEqual(len(s1), BRAINPOOLP512r1.verifying_key_length)
        pub2 = VerifyingKey.from_string(s1, curve=BRAINPOOLP512r1)
        self.assertTruePubkeysEqual(pub1, pub2)

        pub1_der = pub1.to_der()
        self.assertEqual(type(pub1_der), binary_type)
        pub2 = VerifyingKey.from_der(pub1_der)
        self.assertTruePubkeysEqual(pub1, pub2)

    def test_vk_to_der_with_invalid_point_encoding(self):
        sk = SigningKey.generate()
        vk = sk.verifying_key

        with self.assertRaises(ValueError):
            vk.to_der("raw")

    def test_sk_to_der_with_invalid_point_encoding(self):
        sk = SigningKey.generate()

        with self.assertRaises(ValueError):
            sk.to_der("raw")

    def test_vk_from_der_garbage_after_curve_oid(self):
        type_oid_der = encoded_oid_ecPublicKey
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1)) + b("garbage")
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\x00\xff", None)
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(der.UnexpectedDER):
            VerifyingKey.from_der(to_decode)

    def test_vk_from_der_invalid_key_type(self):
        type_oid_der = der.encode_oid(*(1, 2, 3))
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\x00\xff", None)
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(der.UnexpectedDER):
            VerifyingKey.from_der(to_decode)

    def test_vk_from_der_garbage_after_point_string(self):
        type_oid_der = encoded_oid_ecPublicKey
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\x00\xff", None) + b("garbage")
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(der.UnexpectedDER):
            VerifyingKey.from_der(to_decode)

    def test_vk_from_der_invalid_bitstring(self):
        type_oid_der = encoded_oid_ecPublicKey
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\x08\xff", None)
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(der.UnexpectedDER):
            VerifyingKey.from_der(to_decode)

    def test_vk_from_der_with_invalid_length_of_encoding(self):
        type_oid_der = encoded_oid_ecPublicKey
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\xff" * 64, 0)
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_der(to_decode)

    def test_vk_from_der_with_raw_encoding(self):
        type_oid_der = encoded_oid_ecPublicKey
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        enc_type_der = der.encode_sequence(type_oid_der, curve_oid_der)
        point_der = der.encode_bitstring(b"\xff" * 48, 0)
        to_decode = der.encode_sequence(enc_type_der, point_der)

        with self.assertRaises(der.UnexpectedDER):
            VerifyingKey.from_der(to_decode)

    def test_signature_strings(self):
        priv1 = SigningKey.generate()
        pub1 = priv1.get_verifying_key()
        data = b("data")

        sig = priv1.sign(data)
        self.assertEqual(type(sig), binary_type)
        self.assertEqual(len(sig), NIST192p.signature_length)
        self.assertTrue(pub1.verify(sig, data))

        sig = priv1.sign(data, sigencode=sigencode_strings)
        self.assertEqual(type(sig), tuple)
        self.assertEqual(len(sig), 2)
        self.assertEqual(type(sig[0]), binary_type)
        self.assertEqual(type(sig[1]), binary_type)
        self.assertEqual(len(sig[0]), NIST192p.baselen)
        self.assertEqual(len(sig[1]), NIST192p.baselen)
        self.assertTrue(pub1.verify(sig, data, sigdecode=sigdecode_strings))

        sig_der = priv1.sign(data, sigencode=sigencode_der)
        self.assertEqual(type(sig_der), binary_type)
        self.assertTrue(pub1.verify(sig_der, data, sigdecode=sigdecode_der))

    def test_sig_decode_strings_with_invalid_count(self):
        with self.assertRaises(MalformedSignature):
            sigdecode_strings([b("one"), b("two"), b("three")], 0xFF)

    def test_sig_decode_strings_with_wrong_r_len(self):
        with self.assertRaises(MalformedSignature):
            sigdecode_strings([b("one"), b("two")], 0xFF)

    def test_sig_decode_strings_with_wrong_s_len(self):
        with self.assertRaises(MalformedSignature):
            sigdecode_strings([b("\xa0"), b("\xb0\xff")], 0xFF)

    def test_verify_with_too_long_input(self):
        sk = SigningKey.generate()
        vk = sk.verifying_key

        with self.assertRaises(BadDigestError):
            vk.verify_digest(None, b("\x00") * 128)

    def test_sk_from_secret_exponent_with_wrong_sec_exponent(self):
        with self.assertRaises(MalformedPointError):
            SigningKey.from_secret_exponent(0)

    def test_sk_from_string_with_wrong_len_string(self):
        with self.assertRaises(MalformedPointError):
            SigningKey.from_string(b("\x01"))

    def test_sk_from_der_with_junk_after_sequence(self):
        ver_der = der.encode_integer(1)
        to_decode = der.encode_sequence(ver_der) + b("garbage")

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_der_with_wrong_version(self):
        ver_der = der.encode_integer(0)
        to_decode = der.encode_sequence(ver_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_der_invalid_const_tag(self):
        ver_der = der.encode_integer(1)
        privkey_der = der.encode_octet_string(b("\x00\xff"))
        curve_oid_der = der.encode_oid(*(1, 2, 3))
        const_der = der.encode_constructed(1, curve_oid_der)
        to_decode = der.encode_sequence(ver_der, privkey_der, const_der, curve_oid_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_der_garbage_after_privkey_oid(self):
        ver_der = der.encode_integer(1)
        privkey_der = der.encode_octet_string(b("\x00\xff"))
        curve_oid_der = der.encode_oid(*(1, 2, 3)) + b("garbage")
        const_der = der.encode_constructed(0, curve_oid_der)
        to_decode = der.encode_sequence(ver_der, privkey_der, const_der, curve_oid_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_der_with_short_privkey(self):
        ver_der = der.encode_integer(1)
        privkey_der = der.encode_octet_string(b("\x00\xff"))
        curve_oid_der = der.encode_oid(*(1, 2, 840, 10045, 3, 1, 1))
        const_der = der.encode_constructed(0, curve_oid_der)
        to_decode = der.encode_sequence(ver_der, privkey_der, const_der, curve_oid_der)

        sk = SigningKey.from_der(to_decode)
        self.assertEqual(sk.privkey.secret_multiplier, 255)

    def test_sk_from_p8_der_with_wrong_version(self):
        ver_der = der.encode_integer(2)
        algorithm_der = der.encode_sequence(
            der.encode_oid(1, 2, 840, 10045, 2, 1),
            der.encode_oid(1, 2, 840, 10045, 3, 1, 1),
        )
        privkey_der = der.encode_octet_string(
            der.encode_sequence(
                der.encode_integer(1), der.encode_octet_string(b"\x00\xff")
            )
        )
        to_decode = der.encode_sequence(ver_der, algorithm_der, privkey_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_p8_der_with_wrong_algorithm(self):
        ver_der = der.encode_integer(1)
        algorithm_der = der.encode_sequence(
            der.encode_oid(1, 2, 3), der.encode_oid(1, 2, 840, 10045, 3, 1, 1)
        )
        privkey_der = der.encode_octet_string(
            der.encode_sequence(
                der.encode_integer(1), der.encode_octet_string(b"\x00\xff")
            )
        )
        to_decode = der.encode_sequence(ver_der, algorithm_der, privkey_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_p8_der_with_trailing_junk_after_algorithm(self):
        ver_der = der.encode_integer(1)
        algorithm_der = der.encode_sequence(
            der.encode_oid(1, 2, 840, 10045, 2, 1),
            der.encode_oid(1, 2, 840, 10045, 3, 1, 1),
            der.encode_octet_string(b"junk"),
        )
        privkey_der = der.encode_octet_string(
            der.encode_sequence(
                der.encode_integer(1), der.encode_octet_string(b"\x00\xff")
            )
        )
        to_decode = der.encode_sequence(ver_der, algorithm_der, privkey_der)

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sk_from_p8_der_with_trailing_junk_after_key(self):
        ver_der = der.encode_integer(1)
        algorithm_der = der.encode_sequence(
            der.encode_oid(1, 2, 840, 10045, 2, 1),
            der.encode_oid(1, 2, 840, 10045, 3, 1, 1),
        )
        privkey_der = der.encode_octet_string(
            der.encode_sequence(
                der.encode_integer(1), der.encode_octet_string(b"\x00\xff")
            )
            + der.encode_integer(999)
        )
        to_decode = der.encode_sequence(
            ver_der,
            algorithm_der,
            privkey_der,
            der.encode_octet_string(b"junk"),
        )

        with self.assertRaises(der.UnexpectedDER):
            SigningKey.from_der(to_decode)

    def test_sign_with_too_long_hash(self):
        sk = SigningKey.from_secret_exponent(12)

        with self.assertRaises(BadDigestError):
            sk.sign_digest(b("\xff") * 64)

    def test_hashfunc(self):
        sk = SigningKey.generate(curve=NIST256p, hashfunc=sha256)
        data = b("security level is 128 bits")
        sig = sk.sign(data)
        vk = VerifyingKey.from_string(
            sk.get_verifying_key().to_string(), curve=NIST256p, hashfunc=sha256
        )
        self.assertTrue(vk.verify(sig, data))

        sk2 = SigningKey.generate(curve=NIST256p)
        sig2 = sk2.sign(data, hashfunc=sha256)
        vk2 = VerifyingKey.from_string(
            sk2.get_verifying_key().to_string(),
            curve=NIST256p,
            hashfunc=sha256,
        )
        self.assertTrue(vk2.verify(sig2, data))

        vk3 = VerifyingKey.from_string(
            sk.get_verifying_key().to_string(), curve=NIST256p
        )
        self.assertTrue(vk3.verify(sig, data, hashfunc=sha256))

    def test_public_key_recovery(self):
        # Create keys
        curve = BRAINPOOLP160r1

        sk = SigningKey.generate(curve=curve)
        vk = sk.get_verifying_key()

        # Sign a message
        data = b("blahblah")
        signature = sk.sign(data)

        # Recover verifying keys
        recovered_vks = VerifyingKey.from_public_key_recovery(signature, data, curve)

        # Test if each pk is valid
        for recovered_vk in recovered_vks:
            # Test if recovered vk is valid for the data
            self.assertTrue(recovered_vk.verify(signature, data))

            # Test if properties are equal
            self.assertEqual(vk.curve, recovered_vk.curve)
            self.assertEqual(vk.default_hashfunc, recovered_vk.default_hashfunc)

        # Test if original vk is the list of recovered keys
        self.assertIn(
            vk.pubkey.point,
            [recovered_vk.pubkey.point for recovered_vk in recovered_vks],
        )

    def test_public_key_recovery_with_custom_hash(self):
        # Create keys
        curve = BRAINPOOLP160r1

        sk = SigningKey.generate(curve=curve, hashfunc=sha256)
        vk = sk.get_verifying_key()

        # Sign a message
        data = b("blahblah")
        signature = sk.sign(data)

        # Recover verifying keys
        recovered_vks = VerifyingKey.from_public_key_recovery(
            signature, data, curve, hashfunc=sha256, allow_truncate=True
        )

        # Test if each pk is valid
        for recovered_vk in recovered_vks:
            # Test if recovered vk is valid for the data
            self.assertTrue(recovered_vk.verify(signature, data))

            # Test if properties are equal
            self.assertEqual(vk.curve, recovered_vk.curve)
            self.assertEqual(sha256, recovered_vk.default_hashfunc)

        # Test if original vk is the list of recovered keys
        self.assertIn(
            vk.pubkey.point,
            [recovered_vk.pubkey.point for recovered_vk in recovered_vks],
        )

    def test_encoding(self):
        sk = SigningKey.from_secret_exponent(123456789)
        vk = sk.verifying_key

        exp = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )
        self.assertEqual(vk.to_string(), exp)
        self.assertEqual(vk.to_string("raw"), exp)
        self.assertEqual(vk.to_string("uncompressed"), b("\x04") + exp)
        self.assertEqual(vk.to_string("compressed"), b("\x02") + exp[:24])
        self.assertEqual(vk.to_string("hybrid"), b("\x06") + exp)

    def test_decoding(self):
        sk = SigningKey.from_secret_exponent(123456789)
        vk = sk.verifying_key

        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )

        from_raw = VerifyingKey.from_string(enc)
        self.assertEqual(from_raw.pubkey.point, vk.pubkey.point)

        from_uncompressed = VerifyingKey.from_string(b("\x04") + enc)
        self.assertEqual(from_uncompressed.pubkey.point, vk.pubkey.point)

        from_compressed = VerifyingKey.from_string(b("\x02") + enc[:24])
        self.assertEqual(from_compressed.pubkey.point, vk.pubkey.point)

        from_uncompressed = VerifyingKey.from_string(b("\x06") + enc)
        self.assertEqual(from_uncompressed.pubkey.point, vk.pubkey.point)

    def test_uncompressed_decoding_as_only_alowed(self):
        enc = b(
            "\x04"
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )
        vk = VerifyingKey.from_string(enc, valid_encodings=("uncompressed",))
        sk = SigningKey.from_secret_exponent(123456789)

        self.assertEqual(vk, sk.verifying_key)

    def test_raw_decoding_with_blocked_format(self):
        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )
        with self.assertRaises(MalformedPointError) as exp:
            VerifyingKey.from_string(enc, valid_encodings=("hybrid",))

        self.assertIn("hybrid", str(exp.exception))

    def test_decoding_with_unknown_format(self):
        with self.assertRaises(ValueError) as e:
            VerifyingKey.from_string(b"", valid_encodings=("raw", "foobar"))

        self.assertIn("Only uncompressed, compressed", str(e.exception))

    def test_uncompressed_decoding_with_blocked_format(self):
        enc = b(
            "\x04"
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )
        with self.assertRaises(MalformedPointError) as exp:
            VerifyingKey.from_string(enc, valid_encodings=("hybrid",))

        self.assertIn("Invalid X9.62 encoding", str(exp.exception))

    def test_hybrid_decoding_with_blocked_format(self):
        enc = b(
            "\x06"
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )
        with self.assertRaises(MalformedPointError) as exp:
            VerifyingKey.from_string(enc, valid_encodings=("uncompressed",))

        self.assertIn("Invalid X9.62 encoding", str(exp.exception))

    def test_compressed_decoding_with_blocked_format(self):
        enc = b(
            "\x02"
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )[:25]
        with self.assertRaises(MalformedPointError) as exp:
            VerifyingKey.from_string(enc, valid_encodings=("hybrid", "raw"))

        self.assertIn("(hybrid, raw)", str(exp.exception))

    def test_decoding_with_malformed_uncompressed(self):
        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x02") + enc)

    def test_decoding_with_malformed_compressed(self):
        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x01") + enc[:24])

    def test_decoding_with_inconsistent_hybrid(self):
        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x07") + enc)

    def test_decoding_with_point_not_on_curve(self):
        enc = b(
            "\x0c\xe0\x1d\xe0d\x1c\x8eS\x8a\xc0\x9eK\xa8x !\xd5\xc2\xc3"
            "\xfd\xc8\xa0c\xff\xfb\x02\xb9\xc4\x84)\x1a\x0f\x8b\x87\xa4"
            "z\x8a#\xb5\x97\xecO\xb6\xa0HQ\x89*"
        )

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(enc[:47] + b("\x00"))

    def test_decoding_with_point_at_infinity(self):
        # decoding it is unsupported, as it's not necessary to encode it
        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x00"))

    def test_not_lying_on_curve(self):
        enc = number_to_string(NIST192p.curve.p(), NIST192p.curve.p() + 1)

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x02") + enc)

    def test_from_string_with_invalid_curve_too_short_ver_key_len(self):
        # both verifying_key_length and baselen are calculated internally
        # by the Curve constructor, but since we depend on them verify
        # that inconsistent values are detected
        curve = Curve("test", ecdsa.curve_192, ecdsa.generator_192, (1, 2))
        curve.verifying_key_length = 16
        curve.baselen = 32

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x00") * 16, curve)

    def test_from_string_with_invalid_curve_too_long_ver_key_len(self):
        # both verifying_key_length and baselen are calculated internally
        # by the Curve constructor, but since we depend on them verify
        # that inconsistent values are detected
        curve = Curve("test", ecdsa.curve_192, ecdsa.generator_192, (1, 2))
        curve.verifying_key_length = 16
        curve.baselen = 16

        with self.assertRaises(MalformedPointError):
            VerifyingKey.from_string(b("\x00") * 16, curve)


@pytest.mark.parametrize(
    "val,even", [(i, j) for i in range(256) for j in [True, False]]
)
def test_VerifyingKey_decode_with_small_values(val, even):
    enc = number_to_string(val, NIST192p.order)

    if even:
        enc = b("\x02") + enc
    else:
        enc = b("\x03") + enc

    # small values can both be actual valid public keys and not, verify that
    # only expected exceptions are raised if they are not
    try:
        vk = VerifyingKey.from_string(enc)
        assert isinstance(vk, VerifyingKey)
    except MalformedPointError:
        assert True


params = []
for curve in curves:
    for enc in ["raw", "uncompressed", "compressed", "hybrid"]:
        params.append(pytest.param(curve, enc, id="{0}-{1}".format(curve.name, enc)))


@pytest.mark.parametrize("curve,encoding", params)
def test_VerifyingKey_encode_decode(curve, encoding):
    sk = SigningKey.generate(curve=curve)
    vk = sk.verifying_key

    encoded = vk.to_string(encoding)

    from_enc = VerifyingKey.from_string(encoded, curve=curve)

    assert vk.pubkey.point == from_enc.pubkey.point


class OpenSSL(unittest.TestCase):
    # test interoperability with OpenSSL tools. Note that openssl's ECDSA
    # sign/verify arguments changed between 0.9.8 and 1.0.0: the early
    # versions require "-ecdsa-with-SHA1", the later versions want just
    # "-SHA1" (or to leave out that argument entirely, which means the
    # signature will use some default digest algorithm, probably determined
    # by the key, probably always SHA1).
    #
    # openssl ecparam -name secp224r1 -genkey -out privkey.pem
    # openssl ec -in privkey.pem -text -noout # get the priv/pub keys
    # openssl dgst -ecdsa-with-SHA1 -sign privkey.pem -out data.sig data.txt
    # openssl asn1parse -in data.sig -inform DER
    #  data.sig is 64 bytes, probably 56b plus ASN1 overhead
    # openssl dgst -ecdsa-with-SHA1 -prverify privkey.pem -signature data.sig data.txt ; echo $?
    # openssl ec -in privkey.pem -pubout -out pubkey.pem
    # openssl ec -in privkey.pem -pubout -outform DER -out pubkey.der

    OPENSSL_SUPPORTED_CURVES = set(
        c.split(":")[0].strip() for c in run_openssl("ecparam -list_curves").split("\n")
    )

    def get_openssl_messagedigest_arg(self, hash_name):
        v = run_openssl("version")
        # e.g. "OpenSSL 1.0.0 29 Mar 2010", or "OpenSSL 1.0.0a 1 Jun 2010",
        # or "OpenSSL 0.9.8o 01 Jun 2010"
        vs = v.split()[1].split(".")
        if vs >= ["1", "0", "0"]:  # pragma: no cover
            return "-{0}".format(hash_name)
        else:  # pragma: no cover
            return "-ecdsa-with-{0}".format(hash_name)

    # sk: 1:OpenSSL->python  2:python->OpenSSL
    # vk: 3:OpenSSL->python  4:python->OpenSSL
    # sig: 5:OpenSSL->python 6:python->OpenSSL

    @pytest.mark.skipif(
        "secp112r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp112r1",
    )
    def test_from_openssl_secp112r1(self):
        return self.do_test_from_openssl(SECP112r1)

    @pytest.mark.skipif(
        "secp112r2" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp112r2",
    )
    def test_from_openssl_secp112r2(self):
        return self.do_test_from_openssl(SECP112r2)

    @pytest.mark.skipif(
        "secp128r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp128r1",
    )
    def test_from_openssl_secp128r1(self):
        return self.do_test_from_openssl(SECP128r1)

    @pytest.mark.skipif(
        "secp160r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp160r1",
    )
    def test_from_openssl_secp160r1(self):
        return self.do_test_from_openssl(SECP160r1)

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_from_openssl_nist192p(self):
        return self.do_test_from_openssl(NIST192p)

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_from_openssl_nist192p_sha256(self):
        return self.do_test_from_openssl(NIST192p, "SHA256")

    @pytest.mark.skipif(
        "secp224r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp224r1",
    )
    def test_from_openssl_nist224p(self):
        return self.do_test_from_openssl(NIST224p)

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_from_openssl_nist256p(self):
        return self.do_test_from_openssl(NIST256p)

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_from_openssl_nist256p_sha384(self):
        return self.do_test_from_openssl(NIST256p, "SHA384")

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_from_openssl_nist256p_sha512(self):
        return self.do_test_from_openssl(NIST256p, "SHA512")

    @pytest.mark.skipif(
        "secp384r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp384r1",
    )
    def test_from_openssl_nist384p(self):
        return self.do_test_from_openssl(NIST384p)

    @pytest.mark.skipif(
        "secp521r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp521r1",
    )
    def test_from_openssl_nist521p(self):
        return self.do_test_from_openssl(NIST521p)

    @pytest.mark.skipif(
        "secp256k1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp256k1",
    )
    def test_from_openssl_secp256k1(self):
        return self.do_test_from_openssl(SECP256k1)

    @pytest.mark.skipif(
        "brainpoolP160r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP160r1",
    )
    def test_from_openssl_brainpoolp160r1(self):
        return self.do_test_from_openssl(BRAINPOOLP160r1)

    @pytest.mark.skipif(
        "brainpoolP192r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP192r1",
    )
    def test_from_openssl_brainpoolp192r1(self):
        return self.do_test_from_openssl(BRAINPOOLP192r1)

    @pytest.mark.skipif(
        "brainpoolP224r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP224r1",
    )
    def test_from_openssl_brainpoolp224r1(self):
        return self.do_test_from_openssl(BRAINPOOLP224r1)

    @pytest.mark.skipif(
        "brainpoolP256r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP256r1",
    )
    def test_from_openssl_brainpoolp256r1(self):
        return self.do_test_from_openssl(BRAINPOOLP256r1)

    @pytest.mark.skipif(
        "brainpoolP320r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP320r1",
    )
    def test_from_openssl_brainpoolp320r1(self):
        return self.do_test_from_openssl(BRAINPOOLP320r1)

    @pytest.mark.skipif(
        "brainpoolP384r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP384r1",
    )
    def test_from_openssl_brainpoolp384r1(self):
        return self.do_test_from_openssl(BRAINPOOLP384r1)

    @pytest.mark.skipif(
        "brainpoolP512r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP512r1",
    )
    def test_from_openssl_brainpoolp512r1(self):
        return self.do_test_from_openssl(BRAINPOOLP512r1)

    def do_test_from_openssl(self, curve, hash_name="SHA1"):
        curvename = curve.openssl_name
        assert curvename
        # OpenSSL: create sk, vk, sign.
        # Python: read vk(3), checksig(5), read sk(1), sign, check
        mdarg = self.get_openssl_messagedigest_arg(hash_name)
        if os.path.isdir("t"):  # pragma: no cover
            shutil.rmtree("t")
        os.mkdir("t")
        run_openssl("ecparam -name %s -genkey -out t/privkey.pem" % curvename)
        run_openssl("ec -in t/privkey.pem -pubout -out t/pubkey.pem")
        data = b("data")
        with open("t/data.txt", "wb") as e:
            e.write(data)
        run_openssl("dgst %s -sign t/privkey.pem -out t/data.sig t/data.txt" % mdarg)
        run_openssl(
            "dgst %s -verify t/pubkey.pem -signature t/data.sig t/data.txt" % mdarg
        )
        with open("t/pubkey.pem", "rb") as e:
            pubkey_pem = e.read()
        vk = VerifyingKey.from_pem(pubkey_pem)  # 3
        with open("t/data.sig", "rb") as e:
            sig_der = e.read()
        self.assertTrue(
            vk.verify(
                sig_der,
                data,  # 5
                hashfunc=partial(hashlib.new, hash_name),
                sigdecode=sigdecode_der,
            )
        )

        with open("t/privkey.pem") as e:
            fp = e.read()
        sk = SigningKey.from_pem(fp)  # 1
        sig = sk.sign(data, hashfunc=partial(hashlib.new, hash_name))
        self.assertTrue(vk.verify(sig, data, hashfunc=partial(hashlib.new, hash_name)))

        run_openssl(
            "pkcs8 -topk8 -nocrypt "
            "-in t/privkey.pem -outform pem -out t/privkey-p8.pem"
        )
        with open("t/privkey-p8.pem", "rb") as e:
            privkey_p8_pem = e.read()
        sk_from_p8 = SigningKey.from_pem(privkey_p8_pem)
        self.assertEqual(sk, sk_from_p8)

    @pytest.mark.skipif(
        "secp112r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp112r1",
    )
    def test_to_openssl_secp112r1(self):
        self.do_test_to_openssl(SECP112r1)

    @pytest.mark.skipif(
        "secp112r2" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp112r2",
    )
    def test_to_openssl_secp112r2(self):
        self.do_test_to_openssl(SECP112r2)

    @pytest.mark.skipif(
        "secp128r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp128r1",
    )
    def test_to_openssl_secp128r1(self):
        self.do_test_to_openssl(SECP128r1)

    @pytest.mark.skipif(
        "secp160r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp160r1",
    )
    def test_to_openssl_secp160r1(self):
        self.do_test_to_openssl(SECP160r1)

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_to_openssl_nist192p(self):
        self.do_test_to_openssl(NIST192p)

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_to_openssl_nist192p_sha256(self):
        self.do_test_to_openssl(NIST192p, "SHA256")

    @pytest.mark.skipif(
        "secp224r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp224r1",
    )
    def test_to_openssl_nist224p(self):
        self.do_test_to_openssl(NIST224p)

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_to_openssl_nist256p(self):
        self.do_test_to_openssl(NIST256p)

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_to_openssl_nist256p_sha384(self):
        self.do_test_to_openssl(NIST256p, "SHA384")

    @pytest.mark.skipif(
        "prime256v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime256v1",
    )
    def test_to_openssl_nist256p_sha512(self):
        self.do_test_to_openssl(NIST256p, "SHA512")

    @pytest.mark.skipif(
        "secp384r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp384r1",
    )
    def test_to_openssl_nist384p(self):
        self.do_test_to_openssl(NIST384p)

    @pytest.mark.skipif(
        "secp521r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp521r1",
    )
    def test_to_openssl_nist521p(self):
        self.do_test_to_openssl(NIST521p)

    @pytest.mark.skipif(
        "secp256k1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support secp256k1",
    )
    def test_to_openssl_secp256k1(self):
        self.do_test_to_openssl(SECP256k1)

    @pytest.mark.skipif(
        "brainpoolP160r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP160r1",
    )
    def test_to_openssl_brainpoolp160r1(self):
        self.do_test_to_openssl(BRAINPOOLP160r1)

    @pytest.mark.skipif(
        "brainpoolP192r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP192r1",
    )
    def test_to_openssl_brainpoolp192r1(self):
        self.do_test_to_openssl(BRAINPOOLP192r1)

    @pytest.mark.skipif(
        "brainpoolP224r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP224r1",
    )
    def test_to_openssl_brainpoolp224r1(self):
        self.do_test_to_openssl(BRAINPOOLP224r1)

    @pytest.mark.skipif(
        "brainpoolP256r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP256r1",
    )
    def test_to_openssl_brainpoolp256r1(self):
        self.do_test_to_openssl(BRAINPOOLP256r1)

    @pytest.mark.skipif(
        "brainpoolP320r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP320r1",
    )
    def test_to_openssl_brainpoolp320r1(self):
        self.do_test_to_openssl(BRAINPOOLP320r1)

    @pytest.mark.skipif(
        "brainpoolP384r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP384r1",
    )
    def test_to_openssl_brainpoolp384r1(self):
        self.do_test_to_openssl(BRAINPOOLP384r1)

    @pytest.mark.skipif(
        "brainpoolP512r1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support brainpoolP512r1",
    )
    def test_to_openssl_brainpoolp512r1(self):
        self.do_test_to_openssl(BRAINPOOLP512r1)

    def do_test_to_openssl(self, curve, hash_name="SHA1"):
        curvename = curve.openssl_name
        assert curvename
        # Python: create sk, vk, sign.
        # OpenSSL: read vk(4), checksig(6), read sk(2), sign, check
        mdarg = self.get_openssl_messagedigest_arg(hash_name)
        if os.path.isdir("t"):  # pragma: no cover
            shutil.rmtree("t")
        os.mkdir("t")
        sk = SigningKey.generate(curve=curve)
        vk = sk.get_verifying_key()
        data = b("data")
        with open("t/pubkey.der", "wb") as e:
            e.write(vk.to_der())  # 4
        with open("t/pubkey.pem", "wb") as e:
            e.write(vk.to_pem())  # 4
        sig_der = sk.sign(
            data,
            hashfunc=partial(hashlib.new, hash_name),
            sigencode=sigencode_der,
        )

        with open("t/data.sig", "wb") as e:
            e.write(sig_der)  # 6
        with open("t/data.txt", "wb") as e:
            e.write(data)
        with open("t/baddata.txt", "wb") as e:
            e.write(data + b("corrupt"))

        self.assertRaises(
            SubprocessError,
            run_openssl,
            "dgst %s -verify t/pubkey.der -keyform DER -signature t/data.sig t/baddata.txt"
            % mdarg,
        )
        run_openssl(
            "dgst %s -verify t/pubkey.der -keyform DER -signature t/data.sig t/data.txt"
            % mdarg
        )

        with open("t/privkey.pem", "wb") as e:
            e.write(sk.to_pem())  # 2
        run_openssl("dgst %s -sign t/privkey.pem -out t/data.sig2 t/data.txt" % mdarg)
        run_openssl(
            "dgst %s -verify t/pubkey.pem -signature t/data.sig2 t/data.txt" % mdarg
        )

        with open("t/privkey-explicit.pem", "wb") as e:
            e.write(sk.to_pem(curve_parameters_encoding="explicit"))
        run_openssl(
            "dgst %s -sign t/privkey-explicit.pem -out t/data.sig2 t/data.txt" % mdarg
        )
        run_openssl(
            "dgst %s -verify t/pubkey.pem -signature t/data.sig2 t/data.txt" % mdarg
        )

        with open("t/privkey-p8.pem", "wb") as e:
            e.write(sk.to_pem(format="pkcs8"))
        run_openssl(
            "dgst %s -sign t/privkey-p8.pem -out t/data.sig3 t/data.txt" % mdarg
        )
        run_openssl(
            "dgst %s -verify t/pubkey.pem -signature t/data.sig3 t/data.txt" % mdarg
        )

        with open("t/privkey-p8-explicit.pem", "wb") as e:
            e.write(sk.to_pem(format="pkcs8", curve_parameters_encoding="explicit"))
        run_openssl(
            "dgst %s -sign t/privkey-p8-explicit.pem -out t/data.sig3 t/data.txt"
            % mdarg
        )
        run_openssl(
            "dgst %s -verify t/pubkey.pem -signature t/data.sig3 t/data.txt" % mdarg
        )


class TooSmallCurve(unittest.TestCase):
    OPENSSL_SUPPORTED_CURVES = set(
        c.split(":")[0].strip() for c in run_openssl("ecparam -list_curves").split("\n")
    )

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_sign_too_small_curve_dont_allow_truncate_raises(self):
        sk = SigningKey.generate(curve=NIST192p)
        data = b("data")
        with self.assertRaises(BadDigestError):
            sk.sign(
                data,
                hashfunc=partial(hashlib.new, "SHA256"),
                sigencode=sigencode_der,
                allow_truncate=False,
            )

    @pytest.mark.skipif(
        "prime192v1" not in OPENSSL_SUPPORTED_CURVES,
        reason="system openssl does not support prime192v1",
    )
    def test_verify_too_small_curve_dont_allow_truncate_raises(self):
        sk = SigningKey.generate(curve=NIST192p)
        vk = sk.get_verifying_key()
        data = b("data")
        sig_der = sk.sign(
            data,
            hashfunc=partial(hashlib.new, "SHA256"),
            sigencode=sigencode_der,
            allow_truncate=True,
        )
        with self.assertRaises(BadDigestError):
            vk.verify(
                sig_der,
                data,
                hashfunc=partial(hashlib.new, "SHA256"),
                sigdecode=sigdecode_der,
                allow_truncate=False,
            )


class DER(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(der.encode_integer(0), b("\x02\x01\x00"))
        self.assertEqual(der.encode_integer(1), b("\x02\x01\x01"))
        self.assertEqual(der.encode_integer(127), b("\x02\x01\x7f"))
        self.assertEqual(der.encode_integer(128), b("\x02\x02\x00\x80"))
        self.assertEqual(der.encode_integer(256), b("\x02\x02\x01\x00"))
        # self.assertEqual(der.encode_integer(-1), b("\x02\x01\xff"))

        def s(n):
            return der.remove_integer(der.encode_integer(n) + b("junk"))

        self.assertEqual(s(0), (0, b("junk")))
        self.assertEqual(s(1), (1, b("junk")))
        self.assertEqual(s(127), (127, b("junk")))
        self.assertEqual(s(128), (128, b("junk")))
        self.assertEqual(s(256), (256, b("junk")))
        self.assertEqual(
            s(1234567890123456789012345678901234567890),
            (1234567890123456789012345678901234567890, b("junk")),
        )

    def test_number(self):
        self.assertEqual(der.encode_number(0), b("\x00"))
        self.assertEqual(der.encode_number(127), b("\x7f"))
        self.assertEqual(der.encode_number(128), b("\x81\x00"))
        self.assertEqual(der.encode_number(3 * 128 + 7), b("\x83\x07"))
        # self.assertEqual(der.read_number("\x81\x9b" + "more"), (155, 2))
        # self.assertEqual(der.encode_number(155), b("\x81\x9b"))
        for n in (0, 1, 2, 127, 128, 3 * 128 + 7, 840, 10045):  # , 155):
            x = der.encode_number(n) + b("more")
            n1, llen = der.read_number(x)
            self.assertEqual(n1, n)
            self.assertEqual(x[llen:], b("more"))

    def test_length(self):
        self.assertEqual(der.encode_length(0), b("\x00"))
        self.assertEqual(der.encode_length(127), b("\x7f"))
        self.assertEqual(der.encode_length(128), b("\x81\x80"))
        self.assertEqual(der.encode_length(255), b("\x81\xff"))
        self.assertEqual(der.encode_length(256), b("\x82\x01\x00"))
        self.assertEqual(der.encode_length(3 * 256 + 7), b("\x82\x03\x07"))
        self.assertEqual(der.read_length(b("\x81\x9b") + b("more")), (155, 2))
        self.assertEqual(der.encode_length(155), b("\x81\x9b"))
        for n in (0, 1, 2, 127, 128, 255, 256, 3 * 256 + 7, 155):
            x = der.encode_length(n) + b("more")
            n1, llen = der.read_length(x)
            self.assertEqual(n1, n)
            self.assertEqual(x[llen:], b("more"))

    def test_sequence(self):
        x = der.encode_sequence(b("ABC"), b("DEF")) + b("GHI")
        self.assertEqual(x, b("\x30\x06ABCDEFGHI"))
        x1, rest = der.remove_sequence(x)
        self.assertEqual(x1, b("ABCDEF"))
        self.assertEqual(rest, b("GHI"))

    def test_constructed(self):
        x = der.encode_constructed(0, NIST224p.encoded_oid)
        self.assertEqual(hexlify(x), b("a007") + b("06052b81040021"))
        x = der.encode_constructed(1, unhexlify(b("0102030a0b0c")))
        self.assertEqual(hexlify(x), b("a106") + b("0102030a0b0c"))


class Util(unittest.TestCase):
    def test_trytryagain(self):
        tta = util.randrange_from_seed__trytryagain
        for i in range(1000):
            seed = "seed-%d" % i
            for order in (
                2**8 - 2,
                2**8 - 1,
                2**8,
                2**8 + 1,
                2**8 + 2,
                2**16 - 1,
                2**16 + 1,
            ):
                n = tta(seed, order)
                self.assertTrue(1 <= n < order, (1, n, order))
        # this trytryagain *does* provide long-term stability
        self.assertEqual(
            ("%x" % (tta("seed", NIST224p.order))).encode(),
            b("6fa59d73bf0446ae8743cf748fc5ac11d5585a90356417e97155c3bc"),
        )

    def test_trytryagain_single(self):
        tta = util.randrange_from_seed__trytryagain
        order = 2**8 - 2
        seed = b"text"
        n = tta(seed, order)
        # known issue: https://github.com/warner/python-ecdsa/issues/221
        if sys.version_info < (3, 0):  # pragma: no branch
            self.assertEqual(n, 228)
        else:
            self.assertEqual(n, 18)

    @given(st.integers(min_value=0, max_value=10**200))
    def test_randrange(self, i):
        # util.randrange does not provide long-term stability: we might
        # change the algorithm in the future.
        entropy = util.PRNG("seed-%d" % i)
        for order in (
            2**8 - 2,
            2**8 - 1,
            2**8,
            2**16 - 1,
            2**16 + 1,
        ):
            # that oddball 2**16+1 takes half our runtime
            n = util.randrange(order, entropy=entropy)
            self.assertTrue(1 <= n < order, (1, n, order))

    def OFF_test_prove_uniformity(self):  # pragma: no cover
        order = 2**8 - 2
        counts = dict([(i, 0) for i in range(1, order)])
        assert 0 not in counts
        assert order not in counts
        for i in range(1000000):
            seed = "seed-%d" % i
            n = util.randrange_from_seed__trytryagain(seed, order)
            counts[n] += 1
        # this technique should use the full range
        self.assertTrue(counts[order - 1])
        for i in range(1, order):
            print_("%3d: %s" % (i, "*" * (counts[i] // 100)))


class RFC6979(unittest.TestCase):
    # https://tools.ietf.org/html/rfc6979#appendix-A.1
    def _do(self, generator, secexp, hsh, hash_func, expected):
        actual = rfc6979.generate_k(generator.order(), secexp, hash_func, hsh)
        self.assertEqual(expected, actual)

    def test_SECP256k1(self):
        """RFC doesn't contain test vectors for SECP256k1 used in bitcoin.
        This vector has been computed by Golang reference implementation instead."""
        self._do(
            generator=SECP256k1.generator,
            secexp=int("9d0219792467d7d37b4d43298a7d0c05", 16),
            hsh=sha256(b("sample")).digest(),
            hash_func=sha256,
            expected=int(
                "8fa1f95d514760e498f28957b824ee6ec39ed64826ff4fecc2b5739ec45b91cd",
                16,
            ),
        )

    def test_SECP256k1_2(self):
        self._do(
            generator=SECP256k1.generator,
            secexp=int(
                "cca9fbcc1b41e5a95d369eaa6ddcff73b61a4efaa279cfc6567e8daa39cbaf50",
                16,
            ),
            hsh=sha256(b("sample")).digest(),
            hash_func=sha256,
            expected=int(
                "2df40ca70e639d89528a6b670d9d48d9165fdc0febc0974056bdce192b8e16a3",
                16,
            ),
        )

    def test_SECP256k1_3(self):
        self._do(
            generator=SECP256k1.generator,
            secexp=0x1,
            hsh=sha256(b("Satoshi Nakamoto")).digest(),
            hash_func=sha256,
            expected=0x8F8A276C19F4149656B280621E358CCE24F5F52542772691EE69063B74F15D15,
        )

    def test_SECP256k1_4(self):
        self._do(
            generator=SECP256k1.generator,
            secexp=0x1,
            hsh=sha256(
                b(
                    "All those moments will be lost in time, like tears in rain. Time to die..."
                )
            ).digest(),
            hash_func=sha256,
            expected=0x38AA22D72376B4DBC472E06C3BA403EE0A394DA63FC58D88686C611ABA98D6B3,
        )

    def test_SECP256k1_5(self):
        self._do(
            generator=SECP256k1.generator,
            secexp=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140,
            hsh=sha256(b("Satoshi Nakamoto")).digest(),
            hash_func=sha256,
            expected=0x33A19B60E25FB6F4435AF53A3D42D493644827367E6453928554F43E49AA6F90,
        )

    def test_SECP256k1_6(self):
        self._do(
            generator=SECP256k1.generator,
            secexp=0xF8B8AF8CE3C7CCA5E300D33939540C10D45CE001B8F252BFBC57BA0342904181,
            hsh=sha256(b("Alan Turing")).digest(),
            hash_func=sha256,
            expected=0x525A82B70E67874398067543FD84C83D30C175FDC45FDEEE082FE13B1D7CFDF1,
        )

    def test_1(self):
        # Basic example of the RFC, it also tests 'try-try-again' from Step H of rfc6979
        self._do(
            generator=Point(
                None,
                0,
                0,
                int("4000000000000000000020108A2E0CC0D99F8A5EF", 16),
            ),
            secexp=int("09A4D6792295A7F730FC3F2B49CBC0F62E862272F", 16),
            hsh=unhexlify(
                b("AF2BDBE1AA9B6EC1E2ADE1D694F41FC71A831D0268E9891562113D8A62ADD1BF")
            ),
            hash_func=sha256,
            expected=int("23AF4074C90A02B3FE61D286D5C87F425E6BDD81B", 16),
        )

    def test_2(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha1(b("sample")).digest(),
            hash_func=sha1,
            expected=int("37D7CA00D2C7B0E5E412AC03BD44BA837FDD5B28CD3B0021", 16),
        )

    def test_3(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha256(b("sample")).digest(),
            hash_func=sha256,
            expected=int("32B1B6D7D42A05CB449065727A84804FB1A3E34D8F261496", 16),
        )

    def test_4(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha512(b("sample")).digest(),
            hash_func=sha512,
            expected=int("A2AC7AB055E4F20692D49209544C203A7D1F2C0BFBC75DB1", 16),
        )

    def test_5(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha1(b("test")).digest(),
            hash_func=sha1,
            expected=int("D9CF9C3D3297D3260773A1DA7418DB5537AB8DD93DE7FA25", 16),
        )

    def test_6(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha256(b("test")).digest(),
            hash_func=sha256,
            expected=int("5C4CE89CF56D9E7C77C8585339B006B97B5F0680B4306C6C", 16),
        )

    def test_7(self):
        self._do(
            generator=NIST192p.generator,
            secexp=int("6FAB034934E4C0FC9AE67F5B5659A9D7D1FEFD187EE09FD4", 16),
            hsh=sha512(b("test")).digest(),
            hash_func=sha512,
            expected=int("0758753A5254759C7CFBAD2E2D9B0792EEE44136C9480527", 16),
        )

    def test_8(self):
        self._do(
            generator=NIST521p.generator,
            secexp=int(
                "0FAD06DAA62BA3B25D2FB40133DA757205DE67F5BB0018FEE8C86E1B68C7E75CAA896EB32F1F47C70855836A6D16FCC1466F6D8FBEC67DB89EC0C08B0E996B83538",
                16,
            ),
            hsh=sha1(b("sample")).digest(),
            hash_func=sha1,
            expected=int(
                "089C071B419E1C2820962321787258469511958E80582E95D8378E0C2CCDB3CB42BEDE42F50E3FA3C71F5A76724281D31D9C89F0F91FC1BE4918DB1C03A5838D0F9",
                16,
            ),
        )

    def test_9(self):
        self._do(
            generator=NIST521p.generator,
            secexp=int(
                "0FAD06DAA62BA3B25D2FB40133DA757205DE67F5BB0018FEE8C86E1B68C7E75CAA896EB32F1F47C70855836A6D16FCC1466F6D8FBEC67DB89EC0C08B0E996B83538",
                16,
            ),
            hsh=sha256(b("sample")).digest(),
            hash_func=sha256,
            expected=int(
                "0EDF38AFCAAECAB4383358B34D67C9F2216C8382AAEA44A3DAD5FDC9C32575761793FEF24EB0FC276DFC4F6E3EC476752F043CF01415387470BCBD8678ED2C7E1A0",
                16,
            ),
        )

    def test_10(self):
        self._do(
            generator=NIST521p.generator,
            secexp=int(
                "0FAD06DAA62BA3B25D2FB40133DA757205DE67F5BB0018FEE8C86E1B68C7E75CAA896EB32F1F47C70855836A6D16FCC1466F6D8FBEC67DB89EC0C08B0E996B83538",
                16,
            ),
            hsh=sha512(b("test")).digest(),
            hash_func=sha512,
            expected=int(
                "16200813020EC986863BEDFC1B121F605C1215645018AEA1A7B215A564DE9EB1B38A67AA1128B80CE391C4FB71187654AAA3431027BFC7F395766CA988C964DC56D",
                16,
            ),
        )


class ECDH(unittest.TestCase):
    def _do(self, curve, generator, dA, x_qA, y_qA, dB, x_qB, y_qB, x_Z, y_Z):
        qA = dA * generator
        qB = dB * generator
        Z = dA * qB
        self.assertEqual(Point(curve, x_qA, y_qA), qA)
        self.assertEqual(Point(curve, x_qB, y_qB), qB)
        self.assertTrue(
            (dA * qB) == (dA * dB * generator) == (dB * dA * generator) == (dB * qA)
        )
        self.assertEqual(Point(curve, x_Z, y_Z), Z)


class RFC6932(ECDH):
    # https://tools.ietf.org/html/rfc6932#appendix-A.1

    def test_brainpoolP224r1(self):
        self._do(
            curve=curve_brainpoolp224r1,
            generator=BRAINPOOLP224r1.generator,
            dA=int("7C4B7A2C8A4BAD1FBB7D79CC0955DB7C6A4660CA64CC4778159B495E", 16),
            x_qA=int("B104A67A6F6E85E14EC1825E1539E8ECDBBF584922367DD88C6BDCF2", 16),
            y_qA=int("46D782E7FDB5F60CD8404301AC5949C58EDB26BC68BA07695B750A94", 16),
            dB=int("63976D4AAE6CD0F6DD18DEFEF55D96569D0507C03E74D6486FFA28FB", 16),
            x_qB=int("2A97089A9296147B71B21A4B574E1278245B536F14D8C2B9D07A874E", 16),
            y_qB=int("9B900D7C77A709A797276B8CA1BA61BB95B546FC29F862E44D59D25B", 16),
            x_Z=int("312DFD98783F9FB77B9704945A73BEB6DCCBE3B65D0F967DCAB574EB", 16),
            y_Z=int("6F800811D64114B1C48C621AB3357CF93F496E4238696A2A012B3C98", 16),
        )

    def test_brainpoolP256r1(self):
        self._do(
            curve=curve_brainpoolp256r1,
            generator=BRAINPOOLP256r1.generator,
            dA=int(
                "041EB8B1E2BC681BCE8E39963B2E9FC415B05283313DD1A8BCC055F11AE" "49699",
                16,
            ),
            x_qA=int(
                "78028496B5ECAAB3C8B6C12E45DB1E02C9E4D26B4113BC4F015F60C5C" "CC0D206",
                16,
            ),
            y_qA=int(
                "A2AE1762A3831C1D20F03F8D1E3C0C39AFE6F09B4D44BBE80CD100987" "B05F92B",
                16,
            ),
            dB=int(
                "06F5240EACDB9837BC96D48274C8AA834B6C87BA9CC3EEDD81F99A16B8D" "804D3",
                16,
            ),
            x_qB=int(
                "8E07E219BA588916C5B06AA30A2F464C2F2ACFC1610A3BE2FB240B635" "341F0DB",
                16,
            ),
            y_qB=int(
                "148EA1D7D1E7E54B9555B6C9AC90629C18B63BEE5D7AA6949EBBF47B2" "4FDE40D",
                16,
            ),
            x_Z=int(
                "05E940915549E9F6A4A75693716E37466ABA79B4BF2919877A16DD2CC2" "E23708",
                16,
            ),
            y_Z=int(
                "6BC23B6702BC5A019438CEEA107DAAD8B94232FFBBC350F3B137628FE6" "FD134C",
                16,
            ),
        )

    def test_brainpoolP384r1(self):
        self._do(
            curve=curve_brainpoolp384r1,
            generator=BRAINPOOLP384r1.generator,
            dA=int(
                "014EC0755B78594BA47FB0A56F6173045B4331E74BA1A6F47322E70D79D"
                "828D97E095884CA72B73FDABD5910DF0FA76A",
                16,
            ),
            x_qA=int(
                "45CB26E4384DAF6FB776885307B9A38B7AD1B5C692E0C32F012533277"
                "8F3B8D3F50CA358099B30DEB5EE69A95C058B4E",
                16,
            ),
            y_qA=int(
                "8173A1C54AFFA7E781D0E1E1D12C0DC2B74F4DF58E4A4E3AF7026C5D3"
                "2DC530A2CD89C859BB4B4B768497F49AB8CC859",
                16,
            ),
            dB=int(
                "6B461CB79BD0EA519A87D6828815D8CE7CD9B3CAA0B5A8262CBCD550A01"
                "5C90095B976F3529957506E1224A861711D54",
                16,
            ),
            x_qB=int(
                "01BF92A92EE4BE8DED1A911125C209B03F99E3161CFCC986DC7711383"
                "FC30AF9CE28CA3386D59E2C8D72CE1E7B4666E8",
                16,
            ),
            y_qB=int(
                "3289C4A3A4FEE035E39BDB885D509D224A142FF9FBCC5CFE5CCBB3026"
                "8EE47487ED8044858D31D848F7A95C635A347AC",
                16,
            ),
            x_Z=int(
                "04CC4FF3DCCCB07AF24E0ACC529955B36D7C807772B92FCBE48F3AFE9A"
                "2F370A1F98D3FA73FD0C0747C632E12F1423EC",
                16,
            ),
            y_Z=int(
                "7F465F90BD69AFB8F828A214EB9716D66ABC59F17AF7C75EE7F1DE22AB"
                "5D05085F5A01A9382D05BF72D96698FE3FF64E",
                16,
            ),
        )

    def test_brainpoolP512r1(self):
        self._do(
            curve=curve_brainpoolp512r1,
            generator=BRAINPOOLP512r1.generator,
            dA=int(
                "636B6BE0482A6C1C41AA7AE7B245E983392DB94CECEA2660A379CFE1595"
                "59E357581825391175FC195D28BAC0CF03A7841A383B95C262B98378287"
                "4CCE6FE333",
                16,
            ),
            x_qA=int(
                "0562E68B9AF7CBFD5565C6B16883B777FF11C199161ECC427A39D17EC"
                "2166499389571D6A994977C56AD8252658BA8A1B72AE42F4FB7532151"
                "AFC3EF0971CCDA",
                16,
            ),
            y_qA=int(
                "A7CA2D8191E21776A89860AFBC1F582FAA308D551C1DC6133AF9F9C3C"
                "AD59998D70079548140B90B1F311AFB378AA81F51B275B2BE6B7DEE97"
                "8EFC7343EA642E",
                16,
            ),
            dB=int(
                "0AF4E7F6D52EDD52907BB8DBAB3992A0BB696EC10DF11892FF205B66D38"
                "1ECE72314E6A6EA079CEA06961DBA5AE6422EF2E9EE803A1F236FB96A17"
                "99B86E5C8B",
                16,
            ),
            x_qB=int(
                "5A7954E32663DFF11AE24712D87419F26B708AC2B92877D6BFEE2BFC4"
                "3714D89BBDB6D24D807BBD3AEB7F0C325F862E8BADE4F74636B97EAAC"
                "E739E11720D323",
                16,
            ),
            y_qB=int(
                "96D14621A9283A1BED84DE8DD64836B2C0758B11441179DC0C54C0D49"
                "A47C03807D171DD544B72CAAEF7B7CE01C7753E2CAD1A861ECA55A719"
                "54EE1BA35E04BE",
                16,
            ),
            x_Z=int(
                "1EE8321A4BBF93B9CF8921AB209850EC9B7066D1984EF08C2BB7232362"
                "08AC8F1A483E79461A00E0D5F6921CE9D360502F85C812BEDEE23AC5B2"
                "10E5811B191E",
                16,
            ),
            y_Z=int(
                "2632095B7B936174B41FD2FAF369B1D18DCADEED7E410A7E251F083109"
                "7C50D02CFED02607B6A2D5ADB4C0006008562208631875B58B54ECDA5A"
                "4F9FE9EAABA6",
                16,
            ),
        )


class RFC7027(ECDH):
    # https://tools.ietf.org/html/rfc7027#appendix-A

    def test_brainpoolP256r1(self):
        self._do(
            curve=curve_brainpoolp256r1,
            generator=BRAINPOOLP256r1.generator,
            dA=int(
                "81DB1EE100150FF2EA338D708271BE38300CB54241D79950F77B0630398" "04F1D",
                16,
            ),
            x_qA=int(
                "44106E913F92BC02A1705D9953A8414DB95E1AAA49E81D9E85F929A8E" "3100BE5",
                16,
            ),
            y_qA=int(
                "8AB4846F11CACCB73CE49CBDD120F5A900A69FD32C272223F789EF10E" "B089BDC",
                16,
            ),
            dB=int(
                "55E40BC41E37E3E2AD25C3C6654511FFA8474A91A0032087593852D3E7D" "76BD3",
                16,
            ),
            x_qB=int(
                "8D2D688C6CF93E1160AD04CC4429117DC2C41825E1E9FCA0ADDD34E6F" "1B39F7B",
                16,
            ),
            y_qB=int(
                "990C57520812BE512641E47034832106BC7D3E8DD0E4C7F1136D70065" "47CEC6A",
                16,
            ),
            x_Z=int(
                "89AFC39D41D3B327814B80940B042590F96556EC91E6AE7939BCE31F3A" "18BF2B",
                16,
            ),
            y_Z=int(
                "49C27868F4ECA2179BFD7D59B1E3BF34C1DBDE61AE12931648F43E5963" "2504DE",
                16,
            ),
        )

    def test_brainpoolP384r1(self):
        self._do(
            curve=curve_brainpoolp384r1,
            generator=BRAINPOOLP384r1.generator,
            dA=int(
                "1E20F5E048A5886F1F157C74E91BDE2B98C8B52D58E5003D57053FC4B0B"
                "D65D6F15EB5D1EE1610DF870795143627D042",
                16,
            ),
            x_qA=int(
                "68B665DD91C195800650CDD363C625F4E742E8134667B767B1B476793"
                "588F885AB698C852D4A6E77A252D6380FCAF068",
                16,
            ),
            y_qA=int(
                "55BC91A39C9EC01DEE36017B7D673A931236D2F1F5C83942D049E3FA2"
                "0607493E0D038FF2FD30C2AB67D15C85F7FAA59",
                16,
            ),
            dB=int(
                "032640BC6003C59260F7250C3DB58CE647F98E1260ACCE4ACDA3DD869F7"
                "4E01F8BA5E0324309DB6A9831497ABAC96670",
                16,
            ),
            x_qB=int(
                "4D44326F269A597A5B58BBA565DA5556ED7FD9A8A9EB76C25F46DB69D"
                "19DC8CE6AD18E404B15738B2086DF37E71D1EB4",
                16,
            ),
            y_qB=int(
                "62D692136DE56CBE93BF5FA3188EF58BC8A3A0EC6C1E151A21038A42E"
                "9185329B5B275903D192F8D4E1F32FE9CC78C48",
                16,
            ),
            x_Z=int(
                "0BD9D3A7EA0B3D519D09D8E48D0785FB744A6B355E6304BC51C229FBBC"
                "E239BBADF6403715C35D4FB2A5444F575D4F42",
                16,
            ),
            y_Z=int(
                "0DF213417EBE4D8E40A5F76F66C56470C489A3478D146DECF6DF0D94BA"
                "E9E598157290F8756066975F1DB34B2324B7BD",
                16,
            ),
        )

    def test_brainpoolP512r1(self):
        self._do(
            curve=curve_brainpoolp512r1,
            generator=BRAINPOOLP512r1.generator,
            dA=int(
                "16302FF0DBBB5A8D733DAB7141C1B45ACBC8715939677F6A56850A38BD8"
                "7BD59B09E80279609FF333EB9D4C061231FB26F92EEB04982A5F1D1764C"
                "AD57665422",
                16,
            ),
            x_qA=int(
                "0A420517E406AAC0ACDCE90FCD71487718D3B953EFD7FBEC5F7F27E28"
                "C6149999397E91E029E06457DB2D3E640668B392C2A7E737A7F0BF044"
                "36D11640FD09FD",
                16,
            ),
            y_qA=int(
                "72E6882E8DB28AAD36237CD25D580DB23783961C8DC52DFA2EC138AD4"
                "72A0FCEF3887CF62B623B2A87DE5C588301EA3E5FC269B373B60724F5"
                "E82A6AD147FDE7",
                16,
            ),
            dB=int(
                "230E18E1BCC88A362FA54E4EA3902009292F7F8033624FD471B5D8ACE49"
                "D12CFABBC19963DAB8E2F1EBA00BFFB29E4D72D13F2224562F405CB8050"
                "3666B25429",
                16,
            ),
            x_qB=int(
                "9D45F66DE5D67E2E6DB6E93A59CE0BB48106097FF78A081DE781CDB31"
                "FCE8CCBAAEA8DD4320C4119F1E9CD437A2EAB3731FA9668AB268D871D"
                "EDA55A5473199F",
                16,
            ),
            y_qB=int(
                "2FDC313095BCDD5FB3A91636F07A959C8E86B5636A1E930E8396049CB"
                "481961D365CC11453A06C719835475B12CB52FC3C383BCE35E27EF194"
                "512B71876285FA",
                16,
            ),
            x_Z=int(
                "A7927098655F1F9976FA50A9D566865DC530331846381C87256BAF3226"
                "244B76D36403C024D7BBF0AA0803EAFF405D3D24F11A9B5C0BEF679FE1"
                "454B21C4CD1F",
                16,
            ),
            y_Z=int(
                "7DB71C3DEF63212841C463E881BDCF055523BD368240E6C3143BD8DEF8"
                "B3B3223B95E0F53082FF5E412F4222537A43DF1C6D25729DDB51620A83"
                "2BE6A26680A2",
                16,
            ),
        )


# https://tools.ietf.org/html/rfc4754#page-5
@pytest.mark.parametrize(
    "w, gwx, gwy, k, msg, md, r, s, curve",
    [
        pytest.param(
            "DC51D3866A15BACDE33D96F992FCA99DA7E6EF0934E7097559C27F1614C88A7F",
            "2442A5CC0ECD015FA3CA31DC8E2BBC70BF42D60CBCA20085E0822CB04235E970",
            "6FC98BD7E50211A4A27102FA3549DF79EBCB4BF246B80945CDDFE7D509BBFD7D",
            "9E56F509196784D963D1C0A401510EE7ADA3DCC5DEE04B154BF61AF1D5A6DECE",
            b"abc",
            sha256,
            "CB28E0999B9C7715FD0A80D8E47A77079716CBBF917DD72E97566EA1C066957C",
            "86FA3BB4E26CAD5BF90B7F81899256CE7594BB1EA0C89212748BFF3B3D5B0315",
            NIST256p,
            id="ECDSA-256",
        ),
        pytest.param(
            "0BEB646634BA87735D77AE4809A0EBEA865535DE4C1E1DCB692E84708E81A5AF"
            "62E528C38B2A81B35309668D73524D9F",
            "96281BF8DD5E0525CA049C048D345D3082968D10FEDF5C5ACA0C64E6465A97EA"
            "5CE10C9DFEC21797415710721F437922",
            "447688BA94708EB6E2E4D59F6AB6D7EDFF9301D249FE49C33096655F5D502FAD"
            "3D383B91C5E7EDAA2B714CC99D5743CA",
            "B4B74E44D71A13D568003D7489908D564C7761E229C58CBFA18950096EB7463B"
            "854D7FA992F934D927376285E63414FA",
            b"abc",
            sha384,
            "FB017B914E29149432D8BAC29A514640B46F53DDAB2C69948084E2930F1C8F7E"
            "08E07C9C63F2D21A07DCB56A6AF56EB3",
            "B263A1305E057F984D38726A1B46874109F417BCA112674C528262A40A629AF1"
            "CBB9F516CE0FA7D2FF630863A00E8B9F",
            NIST384p,
            id="ECDSA-384",
        ),
        pytest.param(
            "0065FDA3409451DCAB0A0EAD45495112A3D813C17BFD34BDF8C1209D7DF58491"
            "20597779060A7FF9D704ADF78B570FFAD6F062E95C7E0C5D5481C5B153B48B37"
            "5FA1",
            "0151518F1AF0F563517EDD5485190DF95A4BF57B5CBA4CF2A9A3F6474725A35F"
            "7AFE0A6DDEB8BEDBCD6A197E592D40188901CECD650699C9B5E456AEA5ADD190"
            "52A8",
            "006F3B142EA1BFFF7E2837AD44C9E4FF6D2D34C73184BBAD90026DD5E6E85317"
            "D9DF45CAD7803C6C20035B2F3FF63AFF4E1BA64D1C077577DA3F4286C58F0AEA"
            "E643",
            "00C1C2B305419F5A41344D7E4359933D734096F556197A9B244342B8B62F46F9"
            "373778F9DE6B6497B1EF825FF24F42F9B4A4BD7382CFC3378A540B1B7F0C1B95"
            "6C2F",
            b"abc",
            sha512,
            "0154FD3836AF92D0DCA57DD5341D3053988534FDE8318FC6AAAAB68E2E6F4339"
            "B19F2F281A7E0B22C269D93CF8794A9278880ED7DBB8D9362CAEACEE54432055"
            "2251",
            "017705A7030290D1CEB605A9A1BB03FF9CDD521E87A696EC926C8C10C8362DF4"
            "975367101F67D1CF9BCCBF2F3D239534FA509E70AAC851AE01AAC68D62F86647"
            "2660",
            NIST521p,
            id="ECDSA-521",
        ),
    ],
)
def test_RFC4754_vectors(w, gwx, gwy, k, msg, md, r, s, curve):
    sk = SigningKey.from_string(unhexlify(w), curve)
    vk = VerifyingKey.from_string(unhexlify(gwx + gwy), curve)
    assert sk.verifying_key == vk
    sig = sk.sign(msg, hashfunc=md, sigencode=sigencode_strings, k=int(k, 16))

    assert sig == (unhexlify(r), unhexlify(s))

    assert vk.verify(sig, msg, md, sigdecode_strings)
