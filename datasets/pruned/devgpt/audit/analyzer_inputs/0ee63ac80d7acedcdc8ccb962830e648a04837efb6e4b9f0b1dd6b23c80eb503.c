void detachMatrix(int **matrix) {
    shmdt(*matrix);
    free(matrix);
}