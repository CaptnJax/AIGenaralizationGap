void drawMesh(mesh_t* mesh, vertexShader_t vertexShader, fragmentShader_t fragShader, void* uniformData) {
    for (int i = 0; i < mesh->numTriangles; i++) {
        triangle_t currentTri = mesh->triangles[i];
        vec3_t transformedVertices[3];
        for (int j = 0; j < 3; j++) {
            int vertexIndex = currentTri.indices[j];
            transformedVertices[j] = vertexShader(&mesh->vertices[vertexIndex], mesh, uniformData);
        }
        rasterizeTriangle(transformedVertices, mesh, fragShader, uniformData);
    }
}