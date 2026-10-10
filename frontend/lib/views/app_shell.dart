import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../viewmodels/auth_viewmodel.dart';
import 'auth_view.dart';
import 'history_view.dart';
import 'home_view.dart';
import 'info_view.dart';

/// Shell con navegacion inferior: de 1 pantalla a 4 sin cambiar la estetica.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  static const _tabs = [
    (title: 'Analizar', subtitle: 'Sube una MRI y obten un diagnostico'),
    (title: 'Historial', subtitle: 'Tus analisis recientes'),
    (title: 'Info', subtitle: 'Aprende sobre cada clase'),
    (title: 'Cuenta', subtitle: 'Perfil opcional'),
  ];

  @override
  Widget build(BuildContext context) {
    final loggedIn = context.watch<AuthViewModel>().isLoggedIn;
    final tab = _tabs[_index];

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 74,
        backgroundColor: Colors.transparent,
        flexibleSpace: Container(
          decoration: const BoxDecoration(gradient: AppTheme.brandGradient),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(tab.title),
            const SizedBox(height: 2),
            Text(
              tab.subtitle,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.82),
                fontSize: 12.5,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.lg),
            child: _StatusDot(loggedIn: loggedIn),
          ),
        ],
      ),
      body: IndexedStack(
        index: _index,
        children: const [
          HomeViewBody(),
          HistoryView(),
          InfoView(),
          AuthView(),
        ],
      ),
      bottomNavigationBar: DecoratedBox(
        decoration: const BoxDecoration(
          color: AppTheme.surface,
          border: Border(top: BorderSide(color: AppTheme.border)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.biotech_outlined),
              selectedIcon: Icon(Icons.biotech),
              label: 'Analizar',
            ),
            NavigationDestination(
              icon: Icon(Icons.history_outlined),
              selectedIcon: Icon(Icons.history),
              label: 'Historial',
            ),
            NavigationDestination(
              icon: Icon(Icons.menu_book_outlined),
              selectedIcon: Icon(Icons.menu_book),
              label: 'Info',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person),
              label: 'Cuenta',
            ),
          ],
        ),
      ),
    );
  }
}

/// Indicador de sesion en el encabezado: punto verde si hay cuenta activa.
class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.loggedIn});

  final bool loggedIn;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: loggedIn ? const Color(0xFF7BE0A4) : Colors.white70,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Text(
            loggedIn ? 'Sesion' : 'Invitado',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// Reexpone el contenido del Home sin su propio Scaffold/AppBar
/// para que viva dentro del shell.
class HomeViewBody extends StatelessWidget {
  const HomeViewBody({super.key});

  @override
  Widget build(BuildContext context) => const HomeViewContent();
}
