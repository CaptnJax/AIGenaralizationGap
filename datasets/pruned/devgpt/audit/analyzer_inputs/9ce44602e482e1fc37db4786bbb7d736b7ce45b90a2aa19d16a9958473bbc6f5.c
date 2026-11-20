vertexOutput_t myVertexShader(const vec3_t* inputVertex, const vec3_t* normal, const mesh_t* mesh, void* uniformData) {
    vertexOutput_t output;
    output.position = *inputVertex;
    output.lighting = (color_t){1.0, 1.0, 1.0};
    return output;
}