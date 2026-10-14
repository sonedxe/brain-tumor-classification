import 'package:brain_tumor_classification/data/services/auth_service.dart';
import 'package:brain_tumor_classification/data/services/session_store.dart';
import 'package:brain_tumor_classification/viewmodels/auth_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _authPayload =
    '{"access_token":"a.b.c","token_type":"bearer","name":"Equipo UNMSM",'
    '"email":"equipo@unmsm.edu.pe","expires_in":604800,"mock":false}';

/// Almacenamiento en memoria: evita el canal de plataforma de SharedPreferences.
class _MemoryStore implements SessionStore {
  String? token;
  String? name;

  @override
  Future<String?> readToken() async => token;

  @override
  Future<String?> readName() async => name;

  @override
  Future<void> save({required String token, required String name}) async {
    this.token = token;
    this.name = name;
  }

  @override
  Future<void> clear() async {
    token = null;
    name = null;
  }
}

AuthViewModel _viewModelWith(MockClient client, _MemoryStore store) {
  final service = AuthService(
    client: client,
    baseUrl: 'http://localhost:8000/api/v1',
  );
  return AuthViewModel(service: service, store: store);
}

void main() {
  group('AuthViewModel', () {
    test('arranca sin sesion', () {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_authPayload, 200)),
        _MemoryStore(),
      );

      expect(viewModel.isLoggedIn, isFalse);
      expect(viewModel.userName, isNull);
    });

    test('login guarda el token y el nombre en el almacenamiento', () async {
      final store = _MemoryStore();
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_authPayload, 200)),
        store,
      );

      final ok = await viewModel.submit(
        email: 'equipo@unmsm.edu.pe',
        password: 'secreto123',
      );

      expect(ok, isTrue);
      expect(viewModel.isLoggedIn, isTrue);
      expect(viewModel.userName, 'Equipo UNMSM');
      expect(store.token, 'a.b.c');
      expect(store.name, 'Equipo UNMSM');
    });

    test('restoreSession repuebla la sesion persistida', () async {
      final store = _MemoryStore()
        ..token = 'x.y.z'
        ..name = 'Equipo UNMSM';
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_authPayload, 200)),
        store,
      );

      await viewModel.restoreSession();

      expect(viewModel.isLoggedIn, isTrue);
      expect(viewModel.userName, 'Equipo UNMSM');
    });

    test('restoreSession no hace nada si no hay token', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_authPayload, 200)),
        _MemoryStore(),
      );

      await viewModel.restoreSession();

      expect(viewModel.isLoggedIn, isFalse);
    });

    test('logout limpia el token del almacenamiento', () async {
      final store = _MemoryStore();
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_authPayload, 200)),
        store,
      );
      await viewModel.submit(email: 'equipo@unmsm.edu.pe', password: 'secreto123');

      await viewModel.logout();

      expect(viewModel.isLoggedIn, isFalse);
      expect(store.token, isNull);
      expect(store.name, isNull);
    });

    test('un error 401 no persiste la sesion', () async {
      final store = _MemoryStore();
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response('{"detail":"Credenciales invalidas"}', 401)),
        store,
      );

      final ok = await viewModel.submit(
        email: 'equipo@unmsm.edu.pe',
        password: 'mala',
      );

      expect(ok, isFalse);
      expect(viewModel.error, contains('Credenciales invalidas'));
      expect(viewModel.isLoggedIn, isFalse);
      expect(store.token, isNull);
    });
  });
}
