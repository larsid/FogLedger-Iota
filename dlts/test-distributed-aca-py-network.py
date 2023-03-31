from typing import List
from fogbed import (
    FogbedExperiment, Container, Resources, Services,
    CloudResourceModel, EdgeResourceModel, FogResourceModel, VirtualInstance,
    setLogLevel, FogbedDistributedExperiment, Worker
)
import time
import os

from indy.indy import (IndyBasic)
setLogLevel('info')



def add_datacenters_to_worker(worker: Worker, datacenters: List[VirtualInstance]):
    for device in datacenters:
        worker.add(device, reachable=True)


if (__name__ == '__main__'):

    exp = FogbedDistributedExperiment()
    worker1 = exp.add_worker(ip='192.168.0.102')
    worker2 = exp.add_worker(ip='192.168.0.105')
    
    # Define Indy network in cloud
    indyCloud = IndyBasic(exp=exp, trustees_path = 'indy/tmp/trustees.csv', prefix='cloud',  number_nodes=3)

    acaPy1 = Container(
        name='aca-py1',
        dimage='aca-py',
        port_bindings={3002: 3002, 3001:3001},
        ports=[3002, 3001],
        environment={
            'ACAPY_ENDPOINT': "http://aries-1:3002",
            'ACAPY_GENESIS_FILE': "/var/lib/indy/fogbed/pool_transactions_genesis",
            'ACAPY_LABEL': "Aries 1 Agent",
            'ACAPY_WALLET_KEY': "secret",
            'ACAPY_WALLET_SEED': "000000000000000000000000Trustee2",
            'ADMIN_PORT': 3001,
            'AGENT_PORT': 3002
        },
        volumes=[
            f'/tmp/indy/cloud:/var/lib/indy/'
        ]
    )
    acaPy2= Container(
        name='aca-py2',
        dimage='aca-py',
        port_bindings={3002: 3004, 3001:3003},
        ports=[3002, 3001],
        environment={
            'ACAPY_ENDPOINT': "http://aries-1:3002",
            'ACAPY_GENESIS_FILE': "/var/lib/indy/fogbed/pool_transactions_genesis",
            'ACAPY_LABEL': "Aries 2 Agent",
            'ACAPY_WALLET_KEY': "secret",
            'ACAPY_WALLET_SEED': "000000000000000000000000Trustee3",
            'ADMIN_PORT': 3001,
            'AGENT_PORT': 3002
        },
        volumes=[
            f'/tmp/indy/cloud:/var/lib/indy/'
        ]
    )
    edge1 = exp.add_virtual_instance('edge1')
    edge2 = exp.add_virtual_instance('edge2')
    exp.add_docker(
        container=acaPy1,
        datacenter=edge1)
    
    exp.add_docker(
        container=acaPy2,
        datacenter=edge2)

    
    add_datacenters_to_worker(worker1, [indyCloud.cli_instance])


    add_datacenters_to_worker(worker1, indyCloud.ledgers[:len(indyCloud.ledgers)//2])
    add_datacenters_to_worker(worker2, indyCloud.ledgers[len(indyCloud.ledgers)//2:])
    add_datacenters_to_worker(worker1, [edge1])
    add_datacenters_to_worker(worker2, [edge2])
    exp.add_tunnel(worker1, worker2)
    try:
        exp.start()
        indyCloud.start_network()
        time.sleep(2)
        acaPy1.cmd('aca-py start --admin 0.0.0.0 3001 --admin-insecure-mode --auto-accept-intro-invitation-requests --auto-accept-invites --auto-accept-requests --auto-ping-connection --auto-provision --debug-connections --inbound-transport http 0.0.0.0 3002 --log-level INFO --outbound-transport http --public-invites --wallet-name fogbed --wallet-type indy > output.log 2>&1 &')
        acaPy2.cmd('aca-py start --admin 0.0.0.0 3001 --admin-insecure-mode --auto-accept-intro-invitation-requests --auto-accept-invites --auto-accept-requests --auto-ping-connection --auto-provision --debug-connections --inbound-transport http 0.0.0.0 3002 --log-level INFO --outbound-transport http --public-invites --wallet-name fogbed --wallet-type indy > output.log 2>&1 &')
        
        input('Press any key...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
