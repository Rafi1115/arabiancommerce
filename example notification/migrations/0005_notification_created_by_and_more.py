import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notification", "0004_alter_notification_unique_together"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_notification",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="usernotificationpreference",
            name="in_app_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="fcmtoken",
            name="token",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="fcmtoken",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fcm_tokens",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("push", "Push Notification"),
                    ("in_app", "In-App Notification"),
                    ("email", "Email Notification"),
                    ("sms", "SMS Notification"),
                ],
                default="push",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="title",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="usernotificationpreference",
            name="email_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="usernotificationpreference",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notification_preference",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="ScheduledNotification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("notification_types", models.JSONField(default=list)),
                ("scheduled_at", models.DateTimeField()),
                (
                    "recipient_type",
                    models.CharField(
                        choices=[("all", "All Users"), ("specific", "Specific Users")],
                        default="all",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("sent_count", models.IntegerField(default=0)),
                ("failed_count", models.IntegerField(default=0)),
                ("data", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_schedules",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "specific_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="scheduled_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-scheduled_at"],
            },
        ),
        migrations.AddField(
            model_name="notification",
            name="scheduled_notification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sent_notifications",
                to="notification.schedulednotification",
            ),
        ),
    ]
