# backend/app/services/usuarios_embeddings_services.py

"""
Service encargado de gestionar los embeddings de usuario.

Responsabilidades:
- Crear o actualizar embeddings de usuario
- Obtener embedding de un usuario
"""

import json
from sqlalchemy.orm import Session

from app.models.usuarios_embeddings_models import UsuarioEmbedding


def obtener_embedding_usuario(db: Session, usuario_id: int):
    """
    Obtiene el embedding de un usuario.
    """

    return db.query(UsuarioEmbedding).filter(
        UsuarioEmbedding.usuario_id == usuario_id
    ).first()


def guardar_embedding_usuario(
    db: Session,
    usuario_id: int,
    vector: list,
    model_version: int = 1
):
    """
    Crea o actualiza el embedding de un usuario (upsert).
    """

    embedding_existente = db.query(UsuarioEmbedding).filter(
        UsuarioEmbedding.usuario_id == usuario_id
    ).first()

    vector_serializado = json.dumps(vector)

    if embedding_existente:
        # UPDATE
        embedding_existente.vector = vector_serializado
        embedding_existente.model_version = model_version

    else:
        # CREATE
        nuevo_embedding = UsuarioEmbedding(
            usuario_id=usuario_id,
            vector=vector_serializado,
            model_version=model_version
        )

        db.add(nuevo_embedding)

    db.commit()

def obtener_vector_usuario(db: Session, usuario_id: int):
    """
    Devuelve el vector del usuario ya deserializado (list).
    """

    embedding = obtener_embedding_usuario(db, usuario_id)

    if not embedding:
        return None

    return json.loads(embedding.vector)

from app.services.publicaciones_services import obtener_publicaciones_interactuadas_por_usuario
from app.services.comercios_embeddings_services import obtener_vector_embedding_comercio


def generar_embedding_usuario(db: Session, usuario_id: int):
    """
    Genera el embedding de un usuario a partir de sus interacciones.

    Estrategia inicial:
    - Obtener publicaciones con las que interactuó
    - Obtener embeddings de sus comercios
    - Promediar vectores
    """

    publicaciones = obtener_publicaciones_interactuadas_por_usuario(
        db=db,
        usuario_id=usuario_id
    )

    if not publicaciones:
        return None

    vectores = []

    for pub in publicaciones:
        vector = obtener_vector_embedding_comercio(
            db=db,
            comercio_id=pub.comercio_id
        )

        if vector:
            vectores.append(vector)

    if not vectores:
        return None

    # Promedio de vectores
    dimension = len(vectores[0])
    vector_promedio = [0.0] * dimension

    for vector in vectores:
        for i in range(dimension):
            vector_promedio[i] += vector[i]

    vector_promedio = [v / len(vectores) for v in vector_promedio]

    return vector_promedio

def regenerar_y_guardar_embedding_usuario(
    db: Session,
    usuario_id: int,
    model_version: int = 1,
):
    """
    Genera el embedding del usuario y lo guarda en BD.
    """

    vector = generar_embedding_usuario(
        db=db,
        usuario_id=usuario_id,
    )

    if not vector:
        return None

    guardar_embedding_usuario(
        db=db,
        usuario_id=usuario_id,
        vector=vector,
        model_version=model_version,
    )

    return vector
