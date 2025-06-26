import logging
import os
import yaml
from anp_open_sdk.anp_sdk_user_data import LocalUserDataManager, did_create_user
import glob

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging

app_config = UnifiedConfig(config_file='anp_open_sdk_framework_demo_agent_unified_config.yaml')
set_global_config(app_config)
setup_logging() # Assumption setup_logging Internal changes have also been implemented. get_global_config()
logger = logging.getLogger(__name__)



AGENT_YAML_PATTERN = "data_user/localhost_9527/agents_config/*/agent_mappings.yaml"

def get_all_agent_yaml_files():
    return glob.glob(AGENT_YAML_PATTERN)

def get_all_used_dids(agent_yaml_files):
    dids = {}
    for yaml_path in agent_yaml_files:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            did = cfg.get("did")
            if did:
                if did in dids:
                    dids[did].append(yaml_path)
                else:
                    dids[did] = [yaml_path]
    return dids

def get_all_user_dids():
    manager = LocalUserDataManager()
    users = manager.get_all_users()
    return {user.did: user.name for user in users if user.did}

def main():
    agent_yaml_files = get_all_agent_yaml_files()
    used_dids = get_all_used_dids(agent_yaml_files)
    user_dids = get_all_user_dids()

    # Check for duplicates
    has_duplicates = False
    for did, files in used_dids.items():
        if len(files) > 1:
            has_duplicates = True
            print(f"❌ DIDRepetition: {did} The following multipleagentUse：")
            for f in files:
                print(f"  - {f}")

    # Check for unbound or non-existent items.did
    has_unbinded = False
    for yaml_path in agent_yaml_files:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        did = cfg.get("did")
        if not did or did not in user_dids:
            has_unbinded = True
            print(f"\n⚠️  {yaml_path} Unbound and validDID。")
            print("Available usersDIDAs follows：")
            unused_dids = {k: v for k, v in user_dids.items() if k not in used_dids}
            for idx, (udid, uname) in enumerate(unused_dids.items(), 1):
                print(f"  [{idx}] {uname} ({udid})")
            print(f"  [N] Create New UserDID")
            choice = input("Please select the item to bind.DIDSerial Number，Or enterNCreate New：").strip()
            if choice.upper() == "N":
                # New User Process
                print("Please enter new user information.：")
                name = input("Username: ")
                host = input("Hostname: ")
                port = input("Port number: ")
                host_dir = input("Host path: ")
                agent_type = input("User type: ")
                params = {
                    'name': name,
                    'host': host,
                    'port': int(port),
                    'dir': host_dir,
                    'type': agent_type,
                }
                did_doc = did_create_user(params)
                if did_doc and "id" in did_doc:
                    new_did = did_doc["id"]
                    print(f"New UserDIDSuccessfully created.: {new_did}")
                    cfg["did"] = new_did
                else:
                    print("Create NewDIDFailure，Skip。")
                    continue
            else:
                try:
                    idx = int(choice) - 1
                    new_did = list(unused_dids.keys())[idx]
                    cfg["did"] = new_did
                    print(f"BoundDID: {new_did}")
                    del unused_dids[new_did]
                except Exception as e:
                    print("Invalid selection，Skip。")
                    continue
            # Write backyaml
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
            print(f"Updated {yaml_path} OfDID。")

    # If there are no duplicates and unbound items do not exist.，ListyamlIn the documentname、didAnd the correspondingusers_dataInsideyamlInsidename
    if not has_duplicates and not has_unbinded:
        print("\nCurrentlyAgentBind relationship with the user.:")
        print("=" * 80)
        print(f"{'AgentName':<20} {'Agent DID':<45} {'Bind User':<20}\n")
        print("-" * 80)
        i = 1
        for yaml_path in agent_yaml_files:
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)

            agent_name = cfg.get("name", "Untitled")
            agent_did = cfg.get("did", "NoneDID")

            # Find the corresponding username.
            user_name = user_dids.get(agent_did, "Unbound")

            print(f"{i}:{agent_name:<20} {agent_did:<45} {user_name:<20}\n")
            i += 1

        print("=" * 80)

if __name__ == "__main__":
    main()