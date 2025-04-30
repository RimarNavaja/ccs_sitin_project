from dbhelper import db
from datetime import datetime

class ResourceMaterial(db.Model):
    __tablename__ = 'resource_materials'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource_type = db.Column(db.String(10), nullable=False) # 'file' or 'link'
    file_path = db.Column(db.String(512), nullable=True) # Relative path for uploaded files
    link_url = db.Column(db.String(512), nullable=True) # URL for online resources
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ResourceMaterial {self.id}: {self.title}>'

    @classmethod
    def get_active_resources(cls):
        """Returns all active resource materials, newest first."""
        return cls.query.filter_by(is_active=True).order_by(cls.uploaded_at.desc()).all()

    @classmethod
    def get_all_resources(cls):
        """Returns all resource materials, newest first."""
        return cls.query.order_by(cls.uploaded_at.desc()).all()

    @classmethod
    def get_resource_by_id(cls, resource_id):
        """Returns a resource material by its ID."""
        return cls.query.get(resource_id)
