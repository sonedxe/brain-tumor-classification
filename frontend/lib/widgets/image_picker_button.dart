import 'dart:io';

import 'package:flutter/material.dart';

import '../../core/theme.dart';

/// Vista previa de la imagen y los controles de seleccion.
///
/// MVVM: solo emite intents al ViewModel. No valida archivos, no hace HTTP y
/// no decide el texto de los errores.
class ImagePickerButton extends StatelessWidget {
  const ImagePickerButton({
    super.key,
    required this.image,
    required this.isBusy,
    required this.onPickGallery,
    required this.onPickCamera,
    required this.onClear,
  });

  final File? image;
  final bool isBusy;
  final VoidCallback onPickGallery;
  final VoidCallback onPickCamera;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Preview(image: image),
        const SizedBox(height: 16),
        if (image == null) ...[
          _SourceTile(
            icon: Icons.photo_library_outlined,
            title: 'Elegir de la galeria',
            onTap: isBusy ? null : onPickGallery,
          ),
          const SizedBox(height: 12),
          _SourceTile(
            icon: Icons.photo_camera_outlined,
            title: 'Tomar una foto',
            onTap: isBusy ? null : onPickCamera,
          ),
        ] else
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: isBusy ? null : onClear,
                  icon: const Icon(Icons.close),
                  label: const Text('Cambiar'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(48),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ),
      ],
    );
  }
}

class _Preview extends StatelessWidget {
  const _Preview({required this.image});

  final File? image;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 260,
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFD5DBE1)),
      ),
      clipBehavior: Clip.antiAlias,
      child: image == null
          ? const Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.monitor_heart_outlined, size: 56, color: AppTheme.muted),
                SizedBox(height: 12),
                Text(
                  'Selecciona una imagen de resonancia magnetica',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppTheme.muted),
                ),
              ],
            )
          : Image.file(
              image!,
              fit: BoxFit.contain,
              errorBuilder: (_, _, _) => const Center(
                child: Icon(Icons.broken_image_outlined,
                    size: 48, color: AppTheme.error),
              ),
            ),
    );
  }
}

class _SourceTile extends StatelessWidget {
  const _SourceTile({
    required this.icon,
    required this.title,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: AppTheme.primary),
        title: Text(title),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
