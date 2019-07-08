s;schema: armada/ChartGroup/v1;kind: ArmadaChartGroup;g
s;schema: armada/Chart/v1;kind: ArmadaChart;g
s;schema: armada/Manifest/v1;kind: ArmadaManifest;g
s;schema: deckhand/CertificateAuthorityKey/v1;kind: DeckhandCertificateAuthorityKey;g
s;schema: deckhand/CertificateAuthority/v1;kind: DeckhandCertificateAuthority;g
s;schema: deckhand/CertificateKey/v1;kind: DeckhandCertificateKey;g
s;schema: deckhand/Certificate/v1;kind: DeckhandCertificate;g
s;schema: 'deckhand/DataSchema/v1';kind: DeckhandDataSchema;g
s;schema: deckhand/DataSchema/v1;kind: DeckhandDataSchema;g
s;schema: deckhand/LayeringPolicy/v1;kind: DeckhandLayeringPolicy;g
s;schema: deckhand/Passphrase/v1;kind: DeckhandPassphrase;g
s;schema: deckhand/PrivateKey/v1;kind: DeckhandPrivateKey;g
s;schema: deckhand/PublicKey/v1;kind: DeckhandPublicKey;g
s;schema: 'drydock/BaremetalNode/v1';kind: DrydockBaremetalNode;g
s;schema: 'drydock/BootAction/v1';kind: DrydockBootAction;g
s;schema: 'drydock/HardwareProfile/v1';kind: DrydockHardwareProfile;g
s;schema: drydock/HostProfile/v1;kind: DrydockHostProfile;g
s;schema: 'drydock/NetworkLink/v1';kind: DrydockNetworkLink;g
s;schema: 'drydock/Network/v1';kind: DrydockNetwork;g
s;schema: 'drydock/Region/v1';kind: DrydockRegion;g
s;schema: pegleg/AccountCatalogue/v1;kind: PeglegAccountCatalogue;g
s;schema: 'pegleg/AppArmorProfile/v1';kind: PeglegAppArmorProfile;g
s;schema: pegleg/AppArmorProfile/v1;kind: PeglegAppArmorProfile;g
s;schema: pegleg/CommonAddresses/v1;kind: PeglegCommonAddresses;g
s;schema: pegleg/CommonSoftwareConfig/v1;kind: PeglegCommonSoftwareConfig;g
s;schema: pegleg/EndpointCatalogue/v1;kind: PeglegEndpointCatalogue;g
s;schema: pegleg/Script/v1;kind: PeglegScript;g
s;schema: 'pegleg/SeccompProfile/v1';kind: PeglegSeccompProfile;g
s;schema: pegleg/SeccompProfile/v1;kind: PeglegSeccompProfile;g
s;schema: pegleg/SiteDefinition/v1;kind: PeglegSiteDefinition;g
s;schema: pegleg/SoftwareVersions/v1;kind: PeglegSoftwareVersions;g
s;schema: promenade/Docker/v1;kind: PromenadeDocker;g
s;schema: promenade/Genesis/v1;kind: PromenadeGenesis;g
s;schema: promenade/HostSystem/v1;kind: PromenadeHostSystem;g
s;schema: promenade/Kubelet/v1;kind: PromenadeKubelet;g
s;schema: promenade/KubernetesNetwork/v1;kind: PromenadeKubernetesNetwork;g
s;schema: promenade/PKICatalog/v1;kind: PromenadePKICatalog;g
s;schema: shipyard/DeploymentConfiguration/v1;kind: ShipyardDeploymentConfiguration;g
s;schema: shipyard/DeploymentStrategy/v1;kind: ShipyardDeploymentStrategy;g
/^kind: Armada/i apiVersion: armada.airshipit.org/v1alpha1
/^kind: Deckhand/i apiVersion: deckhand.airshipit.org/v1alpha1
/^kind: Drydock/i apiVersion: drydock.airshipit.org/v1alpha1
/^kind: Pegleg/i apiVersion: pegleg.airshipit.org/v1alpha1
/^kind: Promenade/i apiVersion: promenade.airshipit.org/v1alpha1
/^kind: Shipyard/i apiVersion: shipyard.airshipit.org/v1alpha1
1,$s;^data:;spec:;g
1,$s;/v1$;;g
/schema: metadata/d
/storagePolicy/d
