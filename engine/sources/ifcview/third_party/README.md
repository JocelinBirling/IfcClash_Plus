# .ifcview reader (IfcOpenShell, LGPL v3)

Copied unchanged from IfcOpenShell `src/ifcviewer/` (commit aaaafdef26e2084be3db3c70ff5ca97920233792), the
reader of the BonsaiViewer cache format (version 19). The LGPL headers are
kept; the files stay under LGPL v3, compatible with the Apache 2.0 licence
of the project (SPEC_OptimisationInCPP, "Compilation").

Files: IfcViewReader.{h,cpp}, IfcViewFormat.h, InstancedGeometry.h,
InstanceCompose.{h,cpp}, VertexQuantization.h. Dependencies: zstd, Eigen.

To update: copy the same files from a newer IfcOpenShell and check
IFCVIEW_VERSION (the engine accepts the version these headers declare).
