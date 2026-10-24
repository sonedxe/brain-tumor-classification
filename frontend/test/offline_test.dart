import 'dart:io';
import 'dart:typed_data';

import 'package:brain_tumor_classification/data/local/local_db.dart';
import 'package:brain_tumor_classification/data/models/pending_prediction.dart';
import 'package:brain_tumor_classification/data/repositories/history_repository.dart';
import 'package:brain_tumor_classification/data/services/api_service.dart';
import 'package:brain_tumor_classification/data/services/connectivity_service.dart';
import 'package:brain_tumor_classification/data/services/session_store.dart';
import 'package:brain_tumor_classification/viewmodels/auth_viewmodel.dart';
import 'package:brain_tumor_classification/viewmodels/history_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

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

Future<LocalDB> _memoryDb(Directory dir) async {
  SharedPreferences.setMockInitialValues({});
  final db = LocalDB(
    rootDir: dir,
    preferences: await SharedPreferences.getInstance(),
  );
  await db.init();
  return db;
}

void main() {
  late Directory tempDir;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('bt_offline_');
  });

  tearDown(() async {
    if (tempDir.existsSync()) {
      await tempDir.delete(recursive: true);
    }
  });

  group('LocalDB', () {
    test('encola y lee predicciones pendientes con su imagen', () async {
      final db = await _memoryDb(tempDir);
      final pending = PendingPrediction(
        localId: 'offline-1',
        label: 'glioma',
        confidence: 0.8,
        probabilities: const {'glioma': 0.8},
        modelVersion: 'mobilenetv3-onnx',
        inferenceMs: 40,
        createdAt: '2026-10-24T12:00:00Z',
        imagePath: '',
      );

      await db.addPending(pending, Uint8List.fromList([1, 2, 3]));

      final stored = await db.readPending();
      expect(stored, hasLength(1));
      expect(stored.first.label, 'glioma');
      expect(await db.readPendingImage('offline-1'), [1, 2, 3]);

      await db.removePending('offline-1');
      expect(await db.readPending(), isEmpty);
    });

    test('guarda cuentas offline y evita duplicados por correo', () async {
      final db = await _memoryDb(tempDir);
      await db.saveAccount(
        const OfflineAccount(
          email: 'a@test.com',
          name: 'A',
          password: 'secreto',
        ),
      );
      await db.saveAccount(
        const OfflineAccount(
          email: 'A@test.com',
          name: 'A2',
          password: 'nuevo',
        ),
      );

      final accounts = await db.readAccounts();
      expect(accounts, hasLength(1));
      expect(accounts.first.name, 'A2');
      expect(accounts.first.pendingSync, isTrue);
    });
  });

  group('HistoryViewModel offline', () {
    test('muestra pendientes y la caché sin tocar la red', () async {
      final db = await _memoryDb(tempDir);
      await db.addPending(
        PendingPrediction(
          localId: 'offline-2',
          label: 'meningioma',
          confidence: 0.7,
          probabilities: const {'meningioma': 0.7},
          modelVersion: 'mobilenetv3-onnx',
          inferenceMs: 30,
          createdAt: '2026-10-24T12:00:00Z',
          imagePath: '',
        ),
        Uint8List.fromList([9]),
      );

      final connectivity = ConnectivityService()..setOnlineForTesting(false);
      final viewModel = HistoryViewModel(
        db: db,
        connectivity: connectivity,
        repository: HistoryRepository(
          apiService: ApiService(
            client: MockClient((_) async => http.Response('', 500)),
            baseUrl: 'http://localhost:8000/api/v1',
          ),
        ),
      );

      await viewModel.load();

      expect(viewModel.status, HistoryStatus.success);
      expect(viewModel.entries, hasLength(1));
      expect(viewModel.entries.first.pendingSync, isTrue);
      expect(viewModel.pendingCount, 1);
    });
  });

  group('AuthViewModel offline', () {
    test('registro y login local sin backend', () async {
      final db = await _memoryDb(tempDir);
      final connectivity = ConnectivityService()..setOnlineForTesting(false);
      final store = _MemoryStore();
      final viewModel = AuthViewModel(
        db: db,
        store: store,
        connectivity: connectivity,
      );

      viewModel.toggleMode(); // registro
      final registered = await viewModel.submit(
        email: 'medico@test.com',
        password: 'clave',
        name: 'Medico',
      );

      expect(registered, isTrue);
      expect(viewModel.isLoggedIn, isTrue);
      expect(viewModel.isOfflineSession, isTrue);
      expect(store.token, startsWith('offline:'));

      await viewModel.logout();
      final logged = await viewModel.submit(
        email: 'medico@test.com',
        password: 'clave',
      );

      expect(logged, isTrue);
      expect(viewModel.userName, 'Medico');
    });

    test('rechaza credenciales locales incorrectas', () async {
      final db = await _memoryDb(tempDir);
      final connectivity = ConnectivityService()..setOnlineForTesting(false);
      final viewModel = AuthViewModel(
        db: db,
        store: _MemoryStore(),
        connectivity: connectivity,
      );

      final ok = await viewModel.submit(
        email: 'nadie@test.com',
        password: 'x',
      );

      expect(ok, isFalse);
      expect(viewModel.error, contains('Credenciales'));
    });
  });
}
