import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../viewmodels/auth_viewmodel.dart';
import '../widgets/primary_gradient_button.dart';

/// Pantalla de cuenta: login / registro en una sola vista (camino opcional).
///
/// Sin sesion la app funciona igual; esto solo existe para el historial
/// por usuario y las capturas del informe.
class AuthView extends StatefulWidget {
  const AuthView({super.key});

  @override
  State<AuthView> createState() => _AuthViewState();
}

class _AuthViewState extends State<AuthView> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthViewModel>(
      builder: (context, auth, _) {
        if (auth.isLoggedIn) {
          return _SignedIn(auth: auth);
        }
        return _AuthForm(
          auth: auth,
          name: _name,
          email: _email,
          password: _password,
        );
      },
    );
  }
}

class _SignedIn extends StatelessWidget {
  const _SignedIn({required this.auth});

  final AuthViewModel auth;

  @override
  Widget build(BuildContext context) {
    final name = auth.userName ?? '';
    final initial = name.trim().isEmpty ? '?' : name.trim()[0].toUpperCase();

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          children: [
            Container(
              width: 92,
              height: 92,
              decoration: BoxDecoration(
                gradient: AppTheme.brandGradient,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primary.withValues(alpha: 0.30),
                    blurRadius: 24,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              alignment: Alignment.center,
              child: Text(
                initial,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 38,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              name.isEmpty ? 'Sesion activa' : 'Hola, $name',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: AppSpacing.xs),
            const Text(
              'Sesion opcional activa. Puedes analizar sin cuenta.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.muted),
            ),
            const SizedBox(height: AppSpacing.xl),
            OutlinedButton.icon(
              onPressed: auth.logout,
              icon: const Icon(Icons.logout),
              label: const Text('Cerrar sesion'),
            ),
          ],
        ),
      ),
    );
  }
}

class _AuthForm extends StatelessWidget {
  const _AuthForm({
    required this.auth,
    required this.name,
    required this.email,
    required this.password,
  });

  final AuthViewModel auth;
  final TextEditingController name;
  final TextEditingController email;
  final TextEditingController password;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(isRegisterMode: auth.isRegisterMode),
          const SizedBox(height: AppSpacing.lg),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (auth.isRegisterMode) ...[
                    TextField(
                      controller: name,
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(
                        labelText: 'Nombre',
                        prefixIcon: Icon(Icons.person_outline),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                  ],
                  TextField(
                    controller: email,
                    keyboardType: TextInputType.emailAddress,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: 'Correo',
                      prefixIcon: Icon(Icons.mail_outline),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  TextField(
                    controller: password,
                    obscureText: true,
                    onSubmitted: (_) => _submit(auth),
                    decoration: const InputDecoration(
                      labelText: 'Contrasena',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                  ),
                  if (auth.error != null) ...[
                    const SizedBox(height: AppSpacing.md),
                    _ErrorText(message: auth.error!),
                  ],
                  const SizedBox(height: AppSpacing.lg),
                  PrimaryGradientButton(
                    label: auth.isRegisterMode ? 'Registrarse' : 'Entrar',
                    icon: auth.isRegisterMode
                        ? Icons.person_add_alt
                        : Icons.login,
                    busy: auth.busy,
                    onPressed: () => _submit(auth),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            onPressed: auth.toggleMode,
            child: Text(auth.isRegisterMode
                ? 'Ya tengo cuenta'
                : 'Quiero registrarme'),
          ),
          const SizedBox(height: AppSpacing.xs),
          const Text(
            'La clasificacion funciona sin cuenta. La sesion solo habilita el '
            'historial por usuario y es un modulo de demostracion.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppTheme.muted, fontSize: 12, height: 1.4),
          ),
        ],
      ),
    );
  }

  void _submit(AuthViewModel auth) {
    auth.submit(
      email: email.text.trim(),
      password: password.text,
      name: name.text.trim(),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.isRegisterMode});

  final bool isRegisterMode;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            gradient: AppTheme.brandGradient,
            borderRadius: BorderRadius.circular(AppRadius.md),
          ),
          child: const Icon(Icons.health_and_safety, color: Colors.white),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                isRegisterMode ? 'Crear cuenta' : 'Iniciar sesion',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const Text(
                'Modulo opcional de demostracion',
                style: TextStyle(color: AppTheme.muted, fontSize: 12.5),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ErrorText extends StatelessWidget {
  const _ErrorText({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppTheme.errorSoft,
        borderRadius: BorderRadius.circular(AppRadius.sm),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, size: 18, color: AppTheme.error),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: AppTheme.error, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
