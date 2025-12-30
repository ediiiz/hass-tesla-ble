.DEFAULT_GOAL := help

update:
	@echo "Getting the latest commit hash from Tesla vehicle-command repository..."
	@echo "Git commit hash: $$(git ls-remote https://github.com/teslamotors/vehicle-command.git main | cut -f1)"
	@echo "Downloading latest protocol files from Tesla vehicle-command repository..."
	curl -s -o car_server.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/car_server.proto"
	curl -s -o common.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/common.proto"
	curl -s -o errors.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/errors.proto"
	curl -s -o keys.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/keys.proto"
	curl -s -o managed_charging.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/managed_charging.proto"
	curl -s -o signatures.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/signatures.proto"
	curl -s -o universal_message.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/universal_message.proto"
	curl -s -o vcsec.proto "https://raw.githubusercontent.com/teslamotors/vehicle-command/main/pkg/protocol/protobuf/vcsec.proto"
	@echo "Protocol files updated successfully!"

generate:
	@echo "Regenerating protobuf files..."
	uv run python -m grpc_tools.protoc --proto_path=. --python_out=../custom_components/tesla_ble/core/proto/ --pyi_out=../custom_components/tesla_ble/core/proto/ *.proto google/protobuf/timestamp.proto
	@echo "Fixing protobuf imports..."
	@# For all .py files generated...
	@# 1. Make local imports relative (e.g., `from . import vcsec_pb2`).
	@# 2. Make the vendored `timestamp_pb2` import relative.
	@# 3. Fix the ugly alias for `timestamp_pb2` and update its usages.
	sed -i -E \
		-e 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' \
		-e 's/^(from google\.protobuf import timestamp_pb2)/from .google.protobuf import timestamp_pb2/' \
		-e 's/ as google_dot_protobuf_dot_timestamp__pb2/ as _timestamp_pb2/' \
		-e 's/google_dot_protobuf_dot_timestamp__pb2\./_timestamp_pb2\./g' \
		../custom_components/tesla_ble/core/proto/*.py
	@# For all .pyi files generated...
	@# 1. Make local imports relative.
	@# 2. Make the vendored `timestamp_pb2` import relative.
	sed -i -E \
		-e 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' \
		-e 's/^(from google\.protobuf import timestamp_pb2)/from .google.protobuf import timestamp_pb2/' \
		../custom_components/tesla_ble/core/proto/*.pyi
	@echo "Protobuf files regenerated successfully!"

help:
	@echo "Makefile commands:"
	@echo "  update    - Download the latest protocol files from the Tesla vehicle-command repo"
	@echo "  generate  - Regenerate protobuf files using nanopb"
