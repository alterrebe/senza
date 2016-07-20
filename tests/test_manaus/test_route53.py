from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from senza.manaus.route53 import (RecordType, Route53, Route53HostedZone,
                                  Route53Record)


def test_hosted_zone_from_boto_dict():
    hosted_zone_dict = {'Config': {'PrivateZone': False},
                        'CallerReference': '0000',
                        'ResourceRecordSetCount': 42,
                        'Id': '/hostedzone/random1',
                        'Name': 'example.com.'}
    hosted_zone = Route53HostedZone.from_boto_dict(hosted_zone_dict)

    assert hosted_zone.id == "/hostedzone/random1"
    assert hosted_zone.name == 'example.com.'
    assert hosted_zone.caller_reference == '0000'
    assert hosted_zone.resource_record_set_count == 42
    assert hosted_zone.config == {'PrivateZone': False}


def test_record_from_boto_dict():
    record_dict = {'Name': 'domain.example.com.',
                   'ResourceRecords': [{'Value': '127.0.0.1'}],
                   'TTL': 600,
                   'Type': 'A'}
    record = Route53Record.from_boto_dict(record_dict)
    assert record.name == 'domain.example.com.'
    assert record.ttl == 600
    assert record.region is None


def test_route53_hosted_zones(monkeypatch):
    m_client = MagicMock()
    m_client.return_value = m_client
    hosted_zone1 = {'Config': {'PrivateZone': False},
                    'CallerReference': '0000',
                    'ResourceRecordSetCount': 42,
                    'Id': '/hostedzone/random1',
                    'Name': 'example.com.'}
    hosted_zone2 = {'Config': {'PrivateZone': False},
                    'CallerReference': '0000',
                    'ResourceRecordSetCount': 7,
                    'Id': '/hostedzone/random2',
                    'Name': 'example.net.'}
    m_client.list_hosted_zones.return_value = {'MaxItems': '100',
                                               'ResponseMetadata': {
                                                   'HTTPStatusCode': 200,
                                                   'RequestId': 'FakeId'},
                                               'HostedZones': [hosted_zone1,
                                                               hosted_zone2],
                                               'IsTruncated': False}
    monkeypatch.setattr('boto3.client', m_client)

    route53 = Route53()
    hosted_zones = list(route53.get_hosted_zones())
    assert len(hosted_zones) == 2
    assert hosted_zones[0].id == '/hostedzone/random1'
    assert hosted_zones[1].name == 'example.net.'

    hosted_zones_com = list(route53.get_hosted_zones('example.com'))
    assert len(hosted_zones_com) == 1
    assert hosted_zones_com[0].name == 'example.com.'

    hosted_zones_com = list(route53.get_hosted_zones('example.com.'))
    assert len(hosted_zones_com) == 1
    assert hosted_zones_com[0].name == 'example.com.'

    hosted_zones_by_id = list(route53.get_hosted_zones(id='/hostedzone/random1'))
    assert len(hosted_zones_by_id) == 1
    assert hosted_zones_by_id[0].name == 'example.com.'


def test_route53_hosted_zones_paginated(monkeypatch):
    m_client = MagicMock()
    m_client.return_value = m_client
    hosted_zone1 = {'Config': {'PrivateZone': False},
                    'CallerReference': '0000',
                    'ResourceRecordSetCount': 42,
                    'Id': '/hostedzone/random1',
                    'Name': 'example.com.'}
    hosted_zone2 = {'Config': {'PrivateZone': False},
                    'CallerReference': '0000',
                    'ResourceRecordSetCount': 7,
                    'Id': '/hostedzone/random2',
                    'Name': 'example.net.'}
    side_effect = [{'MaxItems': '100',
                    'ResponseMetadata': {
                        'HTTPStatusCode': 200,
                        'RequestId': 'FakeId'},
                    'HostedZones': [hosted_zone1],
                    'NextMarker': 'Whatever this is a mock anyway',
                    'IsTruncated': True},
                   {'MaxItems': '100',
                    'ResponseMetadata': {
                        'HTTPStatusCode': 200,
                        'RequestId': 'FakeId'},
                    'HostedZones': [hosted_zone2],
                    'IsTruncated': False}
                   ]
    m_client.list_hosted_zones.side_effect = deepcopy(side_effect)
    monkeypatch.setattr('boto3.client', m_client)

    route53 = Route53()
    hosted_zones = list(route53.get_hosted_zones())
    assert len(hosted_zones) == 2
    assert hosted_zones[0].id == '/hostedzone/random1'
    assert hosted_zones[1].name == 'example.net.'

    m_client.list_hosted_zones.side_effect = deepcopy(side_effect)
    hosted_zones_net = list(route53.get_hosted_zones('example.net'))
    assert len(hosted_zones_net) == 1
    assert hosted_zones_net[0].name == 'example.net.'

    m_client.list_hosted_zones.side_effect = deepcopy(side_effect)
    hosted_zones_com = list(route53.get_hosted_zones('example.com.'))
    assert len(hosted_zones_com) == 1
    assert hosted_zones_com[0].name == 'example.com.'


def test_get_records(monkeypatch):
    m_client = MagicMock()
    m_client.return_value = m_client
    hosted_zone1 = {'Config': {'PrivateZone': False},
                    'CallerReference': '0000',
                    'ResourceRecordSetCount': 42,
                    'Id': '/hostedzone/random1',
                    'Name': 'example.com.'}
    mock_records = [{'Name': 'domain.example.com.',
                     'ResourceRecords': [{'Value': '127.0.0.1'}],
                     'TTL': 600,
                     'Type': 'A'},
                    {'Name': 'domain.example.net.',
                     'ResourceRecords': [{'Value': '127.0.0.1'}],
                     'TTL': 600,
                     'Type': 'A'}
                    ]
    m_client.list_hosted_zones.return_value = {'MaxItems': '100',
                                               'ResponseMetadata': {
                                                   'HTTPStatusCode': 200,
                                                   'RequestId': 'FakeId'},
                                               'HostedZones': [hosted_zone1],
                                               'IsTruncated': False}
    m_client.list_resource_record_sets.return_value = {
        "ResourceRecordSets": mock_records}
    monkeypatch.setattr('boto3.client', m_client)

    route53 = Route53()
    records = list(route53.get_records())
    assert len(records) == 2

    records = list(route53.get_records(name='domain.example.net.'))
    assert len(records) == 1
    assert records[0].name == 'domain.example.net.'

    records = list(route53.get_records(name='domain.example.net'))
    assert len(records) == 1
    assert records[0].name == 'domain.example.net.'


def test_route53_record_boto_dict():
    record1 = Route53Record(name='test1', type='A')
    assert record1.boto_dict == {'Name': 'test1',
                                 'Type': 'A'}

    record2 = Route53Record(name='test1', type='A', ttl=42)
    assert record2.boto_dict == {'Name': 'test1',
                                 'Type': 'A',
                                 'TTL': 42}


def test_hosted_zone_upsert(monkeypatch):
    m_client = MagicMock()
    m_client.return_value = m_client
    monkeypatch.setattr('boto3.client', m_client)

    hosted_zone_dict = {'Config': {'PrivateZone': False},
                        'CallerReference': '0000',
                        'ResourceRecordSetCount': 42,
                        'Id': '/hostedzone/random1',
                        'Name': 'example.com.'}

    record1 = Route53Record(name='test1', type='A')

    hosted_zone = Route53HostedZone.from_boto_dict(hosted_zone_dict)
    change_batch1 = hosted_zone.upsert([record1])
    expected_changes = [{'Action': 'UPSERT',
                         'ResourceRecordSet': {'Name': 'test1',
                                               'Type': 'A'}}]
    assert 'Comment' not in change_batch1
    assert change_batch1['Changes'] == expected_changes
    m_client.change_resource_record_sets.assert_called_once_with(HostedZoneId='/hostedzone/random1',
                                                                 ChangeBatch={'Changes': expected_changes})

    m_client.change_resource_record_sets.reset_mock()
    change_batch2 = hosted_zone.upsert([record1], comment="test")
    assert change_batch2['Comment'] == "test"
    assert change_batch2['Changes'] == [{'Action': 'UPSERT',
                                         'ResourceRecordSet': {'Name': 'test1',
                                                               'Type': 'A'}}]
    m_client.change_resource_record_sets.assert_called_once_with(
        HostedZoneId='/hostedzone/random1',
        ChangeBatch={'Changes': expected_changes,
                     'Comment': 'test'})


def test_hosted_zone_delete(monkeypatch):
    m_client = MagicMock()
    m_client.return_value = m_client
    monkeypatch.setattr('boto3.client', m_client)

    hosted_zone_dict = {'Config': {'PrivateZone': False},
                        'CallerReference': '0000',
                        'ResourceRecordSetCount': 42,
                        'Id': '/hostedzone/random1',
                        'Name': 'example.com.'}

    record1 = Route53Record(name='test1', type='A')

    hosted_zone = Route53HostedZone.from_boto_dict(hosted_zone_dict)
    change_batch1 = hosted_zone.delete([record1])
    expected_changes = [{'Action': 'DELETE',
                         'ResourceRecordSet': {'Name': 'test1',
                                               'Type': 'A'}}]
    assert 'Comment' not in change_batch1
    assert change_batch1['Changes'] == expected_changes
    m_client.change_resource_record_sets.assert_called_once_with(HostedZoneId='/hostedzone/random1',
                                                                 ChangeBatch={'Changes': expected_changes})

    m_client.change_resource_record_sets.reset_mock()
    change_batch2 = hosted_zone.delete([record1], comment="test")
    assert change_batch2['Comment'] == "test"
    assert change_batch2['Changes'] == [{'Action': 'DELETE',
                                         'ResourceRecordSet': {'Name': 'test1',
                                                               'Type': 'A'}}]
    m_client.change_resource_record_sets.assert_called_once_with(
        HostedZoneId='/hostedzone/random1',
        ChangeBatch={'Changes': expected_changes,
                     'Comment': 'test'})


def test_to_alias():
    hz = Route53HostedZone(id='/hostedzone/abc',
                           name='example.com',
                           caller_reference='000',
                           config={},
                           resource_record_set_count=42)
    record_dict = {'Name': 'example.com.',
                   'ResourceRecords': [{'Value': 'mylb-123.region.example.com'}],
                   'TTL': 20,
                   'Type': 'CNAME'}

    cname_record = Route53Record.from_boto_dict(record_dict, hosted_zone=hz)

    record2_dict = {'Name': 'hello-bus-v50.bus.zalan.do.',
                    'Type': 'SOA'}

    soa_record = Route53Record.from_boto_dict(record2_dict, hosted_zone=hz)

    alias_record = cname_record.to_alias()
    assert alias_record.name == cname_record.name
    assert alias_record.type == RecordType.A
    assert not alias_record.resource_records
    expected_target = {'DNSName': 'mylb-123.region.example.com',
                       'EvaluateTargetHealth': False,
                       'HostedZoneId': 'abc'}
    assert alias_record.alias_target == expected_target

    alias_record2 = alias_record.to_alias()
    assert alias_record.boto_dict == alias_record2.boto_dict
    assert alias_record is not alias_record2

    with pytest.raises(NotImplementedError):
        soa_record.to_alias()

    record_elb_dict = {'Name': 'app.example.com',
                       'ResourceRecords': [{'Value': 'mylb-123.eu-central-1.elb.amazonaws.com'}],
                       'TTL': 20,
                       'Type': 'CNAME'}
    elb_record = Route53Record.from_boto_dict(record_elb_dict, hosted_zone=hz)
    alias_elb_record = elb_record.to_alias()
    assert alias_elb_record.alias_target['HostedZoneId'] == 'Z215JYRZR1TBD5'
