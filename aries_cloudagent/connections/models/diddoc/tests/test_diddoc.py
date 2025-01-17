"""
Copyright 2017-2019 Government of Canada
Public Services and Procurement Canada - buyandsell.gc.ca

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import json

from asynctest import TestCase as AsyncTestCase, mock as async_mock

from aries_cloudagent.messaging.valid import DID_PREFIX
from .. import DIDDoc, PublicKey, PublicKeyType, Service
from ..util import canon_did, canon_ref


class TestDIDDoc(AsyncTestCase):
    async def test_basic(self):

        # One authn key by reference
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": "3",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC X...",
                },
                {
                    "id": "4",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC 9...",
                },
                {
                    "id": "6",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC A...",
                },
            ],
            "authentication": [
                {
                    "type": "RsaSignatureAuthentication2018",
                    "publicKey": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#4",
                }
            ],
            "service": [
                {
                    "id": "0",
                    "type": "Agency",
                    "serviceEndpoint": f"{DID_PREFIX}:Q4zqM7aXqm7gDQkUVLng9h",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert str(dd) == f"DIDDoc({canon_did(dd_in['id'])})"
        assert len(dd.pubkey) == len(dd_in["publicKey"])
        assert len(dd.authnkey) == len(dd_in["authentication"])

        dd_out = dd.serialize()
        # print('\n\n== 1 == DID Doc {} on abbreviated identifiers: {}'.format(dd, ppjson(dd_out)))

        # Exercise JSON, de/serialization
        dd_json = dd.to_json()
        dd_copy = dd.from_json(dd_json)
        assert dd_copy.did == dd.did
        assert all(
            dd_copy.authnkey[k].to_dict() == dd.authnkey[k].to_dict()
            for k in dd_copy.authnkey
        )
        assert {k for k in dd_copy.authnkey} == {k for k in dd.authnkey}
        assert all(
            dd_copy.pubkey[k].to_dict() == dd.pubkey[k].to_dict()
            for k in dd_copy.pubkey
        )
        assert {k for k in dd_copy.pubkey} == {k for k in dd.pubkey}
        assert all(
            dd_copy.service[k].to_dict() == dd.service[k].to_dict()
            for k in dd_copy.service
        )
        assert {k for k in dd_copy.service} == {k for k in dd.service}
        # print('\n\n== 2 == DID Doc de/serialization operates OK:')

        # Exercise accessors
        dd.did = dd_out["id"]
        assert dd.did == canon_did(dd_out["id"])
        with self.assertRaises(ValueError):
            dd.set(["neither a service", "nor a public key"])
        assert dd.service[[k for k in dd.service][0]].did == dd.did
        # print('\n\n== 3 == DID Doc accessors operate OK')

    def test_embedded_authkey(self):
        # One authn key embedded, all possible refs canonical
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": "3",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC X...",
                },
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#4",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC 9...",
                },
            ],
            "authentication": [
                {
                    "type": "RsaSignatureAuthentication2018",
                    "publicKey": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#4",
                },
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#6",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC A...",
                },
            ],
            "service": [
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;0",
                    "type": "Agency",
                    "serviceEndpoint": "https://www.von.ca",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == len(dd_in["publicKey"]) + 1
        assert len(dd.authnkey) == len(dd_in["authentication"])

        dd_out = dd.serialize()
        # print('\n\n== 4 == DID Doc on mixed reference styles, embedded and ref style authn keys: {}'.format(ppjson(dd_out)))

    def test_reference_authkey(self):
        # All references canonical where possible; one authn key embedded and one by reference
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#3",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC X...",
                },
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#4",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC 9...",
                },
            ],
            "authentication": [
                {
                    "type": "RsaSignatureAuthentication2018",
                    "publicKey": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#4",
                },
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#6",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC A...",
                },
            ],
            "service": [
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;0",
                    "type": "DidMessaging",
                    "serviceEndpoint": "https://www.von.ca",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == len(dd_in["publicKey"]) + 1
        assert len(dd.authnkey) == len(dd_in["authentication"])

        dd_out = dd.serialize()
        # print('\n\n== 5 == DID Doc on canonical refs: {}'.format(ppjson(dd_out)))

    def test_minimal(self):
        # Minimal as per indy-agent test suite without explicit identifiers
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "publicKey": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "type": "DidMessaging",
                    "recipientKeys": ["~XXXXXXXXXXXXXXXX"],
                    "serviceEndpoint": "https://www.von.ca",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == len(dd_in["publicKey"])
        assert len(dd.authnkey) == 0

        dd_out = dd.serialize()
        # print('\n\n== 6 == DID Doc miminal style, implcit DID document identifier: {}'.format(
        #    ppjson(dd_out)))

    def test_minimal_ids(self):
        # Minimal + ids as per indy-agent test suite with explicit identifiers; novel service recipient key on raw base58
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": "LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL;indy",
                    "type": "DidMessaging",
                    "priority": 1,
                    "recipientKeys": ["~YYYYYYYYYYYYYYYY"],
                    "serviceEndpoint": "https://www.von.ca",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == 1 + len(dd_in["publicKey"])
        assert len(dd.authnkey) == 0

        dd_out = dd.serialize()
        # print('\n\n== 7 == DID Doc miminal style plus explicit idents and novel raw base58 service recip key: {}'.format(
        #    ppjson(dd_out)))

    def test_minimal_explicit(self):
        # Minimal + ids as per indy-agent test suite with explicit identifiers; novel service recipient key on raw base58
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": "LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                },
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-2",
                    "type": "Ed25519VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~YYYYYYYYYYYYYYYY",
                },
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-3",
                    "type": "Secp256k1VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyHex": "02b97c30de767f084ce3080168ee293053ba33b235d7116a3263d29f1450936b71",
                },
                {
                    "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-4",
                    "type": "RsaVerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyPem": "-----BEGIN PUBLIC A...",
                },
            ],
            "service": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL;indy",
                    "type": "DidMessaging",
                    "priority": 0,
                    "recipientKeys": ["~ZZZZZZZZZZZZZZZZ"],
                    "serviceEndpoint": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;1",
                },
                {
                    "id": "1",
                    "type": "one",
                    "priority": 1,
                    "recipientKeys": [
                        "~XXXXXXXXXXXXXXXX",
                        f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-1",
                    ],
                    "routingKeys": [f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-4"],
                    "serviceEndpoint": "LjgpST2rjsoxYegQDRm7EL;2",
                },
                {
                    "id": "2",
                    "type": "two",
                    "priority": 2,
                    "recipientKeys": [
                        "~XXXXXXXXXXXXXXXX",
                        f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-1",
                    ],
                    "routingKeys": [f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-4"],
                    "serviceEndpoint": "https://www.two.ca/two",
                },
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == 1 + len(dd_in["publicKey"])
        assert len(dd.authnkey) == 0
        assert {s.priority for s in dd.service.values()} == {0, 1, 2}
        assert len(dd.service) == 3
        assert all(
            len(dd.service[k].to_dict()["recipientKeys"]) == 1 for k in dd.service
        )
        assert (
            "routingKeys"
            not in dd.service[f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;indy"].to_dict()
        )
        assert all(
            len(dd.service[k].to_dict()["routingKeys"]) == 1
            for k in (
                f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;1",
                f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL;2",
            )
        )

        dd_out = dd.serialize()
        # print('\n\n== 8 == DID Doc on mixed service routing and recipient keys: {}'.format(ppjson(dd_out)))

        pk = PublicKey(
            dd.did,
            "99",
            "~AAAAAAAAAAAAAAAA",
            PublicKeyType.ED25519_SIG_2018,
            dd.did,
            True,
        )
        assert "PublicKey" in str(pk)
        dd.set(pk)
        assert len(dd.pubkey) == 2 + len(dd_in["publicKey"])
        assert canon_ref(dd.did, "99", "#") in dd.pubkey
        assert len(dd.authnkey) == 1

        service = Service(
            dd.did, "abc", "IndyAgent", [pk], [pk], "http://www.abc.ca/123"
        )
        dd.set(service)
        assert len(dd.service) == 4
        assert canon_ref(dd.did, "abc", ";") in dd.service
        # print('\n\n== 9 == DID Doc adds public key and service via set() OK')

    def test_missing_recipkey(self):
        # Exercise missing service recipient key
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": "LjgpST2rjsoxYegQDRm7EL",
            "publicKey": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": "LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL;indy",
                    "type": "DidMessaging",
                    "priority": 1,
                    "recipientKeys": [f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL#keys-3"],
                    "serviceEndpoint": "https://www.von.ca",
                }
            ],
        }

        with self.assertRaises(ValueError):
            dd = DIDDoc.deserialize(dd_in)
        # print('\n\n== 10 == DID Doc on underspecified service key fails as expected')

    def test_w3c_minimal(self):
        # Minimal as per W3C Example 2, draft 0.12
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
            "authentication": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "type": "DidMessaging",
                    "serviceEndpoint": "https://example.com/endpoint/8377464",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)
        assert len(dd.pubkey) == 1
        assert len(dd.authnkey) == 1
        assert len(dd.service) == 1

        dd_out = dd.serialize()
        # print('\n\n== 11 == Minimal DID Doc (no pubkey except authentication) as per W3C spec parses OK: {}'.format(
        #    ppjson(dd_out)))

    def test_no_ident(self):
        # Exercise no-identifier case
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "authentication": [
                {
                    "type": "Ed25519VerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "type": "DidMessaging",
                    "serviceEndpoint": "https://example.com/endpoint/8377464",
                }
            ],
        }

        with self.assertRaises(ValueError):
            dd = DIDDoc.deserialize(dd_in)
        # print('\n\n== 12 == DID Doc without identifier rejected as expected')

    def test_canon_did(self):
        # Exercise reference canonicalization, including failure paths
        valid_did = "LjgpST2rjsoxYegQDRm7EL"

        with self.assertRaises(ValueError):
            canon_ref("not-a-DID", ref=valid_did, delimiter="#")

        with self.assertRaises(ValueError):
            canon_ref(valid_did, ref=f"{DID_PREFIX}:not-a-DID", delimiter="#")

        urlref = (
            "https://www.clafouti-quasar.ca:8443/supply-management/fruit/index.html"
        )
        assert canon_ref(valid_did, ref=urlref) == urlref
        # print('\n\n== 13 == Reference canonicalization operates as expected')

    def test_pubkey_type(self):
        dd_in = {
            "@context": "https://w3id.org/did/v1",
            "id": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
            "authentication": [
                {
                    "id": "LjgpST2rjsoxYegQDRm7EL#keys-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": f"{DID_PREFIX}:LjgpST2rjsoxYegQDRm7EL",
                    "publicKeyBase58": "~XXXXXXXXXXXXXXXX",
                }
            ],
            "service": [
                {
                    "type": "DidMessaging",
                    "serviceEndpoint": "https://example.com/endpoint/8377464",
                }
            ],
        }

        dd = DIDDoc.deserialize(dd_in)

        assert PublicKeyType.get("no-such-type") is None
        pubkey0 = dd.pubkey[[k for k in dd.pubkey][0]]
        was_authn = pubkey0.authn
        pubkey0.authn = not was_authn
        assert pubkey0.authn != was_authn
        # print('\n\n== 14 == Changed authentication setting for DIDDoc {} in public key {}, now {}'.format(
        #    pubkey0.did,
        #    pubkey0.id,
        #    repr(pubkey0)))
