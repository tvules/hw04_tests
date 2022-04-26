from django.forms import ModelForm

from .models import Post


class PostForm(ModelForm):
    """Форма для создания/редактирования нового поста."""

    class Meta:
        model = Post
        fields = ('text', 'group')
