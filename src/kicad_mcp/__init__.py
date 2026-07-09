# Patch missing Units enum in protobuf descriptor pool for kicad-python 0.7.1 compatibility
try:
    from google.protobuf import descriptor_pool
    from google.protobuf import descriptor_pb2
    import kipy.proto.common.types.enums_pb2
    
    pool = descriptor_pool.Default()
    try:
        pool.FindFileByName('common/types/units_patch.proto')
    except KeyError:
        file_proto = descriptor_pb2.FileDescriptorProto()
        file_proto.name = 'common/types/units_patch.proto'
        file_proto.package = 'kiapi.common.types'

        enum_type = file_proto.enum_type.add()
        enum_type.name = 'Units'
        for i, name in enumerate(['INCHES', 'MILS', 'MILLIMETERS', 'AUTOMATIC']):
            val = enum_type.value.add()
            val.name = name
            val.number = i

        pool.Add(file_proto)
except Exception:
    pass
