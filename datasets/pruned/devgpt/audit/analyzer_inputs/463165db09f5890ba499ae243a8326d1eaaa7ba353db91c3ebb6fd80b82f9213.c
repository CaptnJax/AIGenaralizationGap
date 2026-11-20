void drawMesh(mesh_t* mesh, vertexShader_t vertexShader, fragmentShader_t fragShader, void* uniformData, framebuffer_t* fb) {
    for (int i = 0; i < mesh->numTriangles; i++) {
        triangle_t currentTri = mesh->triangles[i];
        vertexOutput_t transformedVertices[3];
        for (int j = 0; j < 3; j++) {
            int vertexIndex = currentTri.indices[j];
            int numAttributes;
            transformedVertices[j] = vertexShader(&mesh->vertices[vertexIndex], uniformData, &numAttributes);
        }
        rasterizeTriangle(transformedVertices, fb, fragShader, uniformData);
    }
}